# SPy Language Guide for Claude Code

## Overview
SPy is a statically-typed variant of Python designed for performance-critical applications. It compiles to C/WASM and provides low-level control while maintaining Python-like syntax.

If during coding you encounter limitations and/or missing features, please add them to "Current limitations" section.

To understand better, read:
  - stdlib/*.spy
  - examples/*.spy (WARNING: some of them are marked as "broken", ignore them)
  - spy/tests/compiler/*.py. In particular, pay attention to which builtin modules/functions are available.


## `main` function
Execution starts with the `main` function, which must return `None`:
```spy
def main() -> None:
    print('hello world')
```

## Type System

### Primitive Types
- **Integer types**: `i32`, `i64`, `int` (platform-dependent)
- **Float types**: `f32`, `f64`, `float`
- **Other**: `bool`, `str`, `None`

### Type Annotations
All function parameters and return types require explicit annotations:
```spy
def add(x: i32, y: i32) -> i32:
    return x + y
```

### Variable Declarations
Variables can be declared explicitly or implicitly:
```spy
# Explicit declaration
x: i32 = 42

# Implicit declaration (type inferred from value)
x = 42
```

## Structs

### Basic Struct Definition
Structs are value types (stack-allocated) and map directly to C structs:
```spy
@struct
class Point:
    x: i32
    y: i32

# Create a struct instance using the default constructor
# By default, __new__ takes all fields in order
p = Point(3, 4)

# Access fields (read-only on stack-allocated structs)
value = p.x + p.y
```

**Key Points:**
- Structs are **immutable** when allocated on the stack
- You cannot mutate struct fields, but you can replace the entire struct with a new value
- By default, `StructName(field1, field2, ...)` creates an instance (calls the default `__new__`)
- Use `Point.__make__(x, y)` as an alternative low-level constructor
- Structs can have methods with explicit `self` parameter
- Structs can be nested

### Struct Methods
```spy
@struct
class Point:
    x: f64
    y: f64

    def hypot(self: Point) -> f64:
        return sqrt(self.x * self.x + self.y * self.y)

# Usage
p = Point(3.0, 4.0)
distance = p.hypot()  # Returns 5.0
```

### Custom Constructors
Custom constructors are defined with `__new__()` and must call `__make__()` with all fields:
```spy
@struct
class Point:
    x: i32
    y: i32

    def __new__() -> Point:
        return Point.__make__(0, 0)

# Usage
p = Point()  # Creates Point(0, 0)
```

You can also define constructors with parameters:
```spy
@struct
class Point:
    x: i32
    y: i32

    def __new__(value: i32) -> Point:
        return Point.__make__(value, value)

# Usage
p = Point(5)  # Creates Point(5, 5)
```

**Important:** Custom `__new__()` methods must always call `StructName.__make__()` with all struct fields in order.

### Working with Immutable Structs
Since stack-allocated structs are immutable, you cannot modify fields directly. Instead, create methods that return new instances:

```spy
@struct
class Counter:
    value: i32

    def increment(self: Counter) -> Counter:
        return Counter(self.value + 1)

# Usage - reassign the variable with the new value
counter = Counter(0)
counter = counter.increment()  # counter.value is now 1
counter = counter.increment()  # counter.value is now 2
```

This pattern is essential for struct-based state management:
```spy
@struct
class Random:
    state: i32

    def next(self: Random) -> Random:
        # Return new Random with updated state
        new_state = (1103515245 * self.state + 12345) & 0x7fffffff
        return Random(new_state)

    def get_value(self: Random) -> i32:
        return self.state

# Usage
rng = Random(42)
rng = rng.next()  # Update to next state
value = rng.get_value()
rng = rng.next()  # Update again
```

## Unsafe Pointers & Memory Management

### Allocating Memory
Use `gc_alloc` from the `unsafe` module to allocate heap memory:
```spy
from unsafe import gc_alloc, ptr

# Allocate array of 5 integers
buf = gc_alloc(i32)(5)
buf[0] = 42

# Allocate a single struct
@struct
class Point:
    x: i32
    y: i32

p = gc_alloc(Point)(1)
p.x = 10
p.y = 20
```

### Pointer Types
Pointers are typed with `ptr[T]`:
```spy
from unsafe import ptr, gc_alloc

def make_point(x: i32, y: i32) -> ptr[Point]:
    p = gc_alloc(Point)(1)
    p.x = x
    p.y = y
    return p
```

### Mutable Structs via Pointers
Unlike stack-allocated structs, pointer-to-structs are **mutable**:
```spy
from unsafe import gc_alloc, ptr

@struct
class Point:
    x: i32
    y: i32

p = gc_alloc(Point)(1)
p.x = 10  # OK: can mutate through pointer
p.y = 20  # OK
```

### Null Pointers
```spy
from unsafe import ptr

null_ptr = ptr[i32].NULL

def is_null(p: ptr[i32]) -> bool:
    if p:
        return False
    else:
        return True
```

### Pointer Equality
```spy
p1 = gc_alloc(i32)(1)
p2 = gc_alloc(i32)(1)
same = (p1 == p1)  # True
different = (p1 == p2)  # False
```

### Self-Referential Structs
```spy
@struct
class Node:
    val: i32
    next: ptr[Node]

def new_node(val: i32) -> ptr[Node]:
    n = gc_alloc(Node)(1)
    n.val = val
    n.next = ptr[Node].NULL
    return n
```

## @blue Functions (Compile-Time Execution)

### Blue Functions
Blue functions execute at compile-time in the Python interpreter:
```spy
@blue
def foo(x):
    # Executes at compile-time
    return 42
```

**Key characteristics:**
- Execute during compilation
- Can manipulate types and return types as values
- Used for metaprogramming and generics
- Variables cannot be redeclared in blue functions

## Generics

### @blue.generic Functions
Generic functions use `@blue.generic` decorator:
```spy
@blue.generic
def add(T):
    def impl(x: T, y: T) -> T:
        return x + y
    return impl

# Usage
result_i32 = add[i32](1, 2)
result_str = add[str]('hello ', 'world')
```

### Generic Structs
```spy
@blue.generic
def List(T):
    @struct
    class ListData:
        length: i32
        capacity: i32
        items: ptr[T]

    @typelift
    class _ListImpl:
        __ll__: ptr[ListData]

        def __new__() -> _ListImpl:
            data = gc_alloc(ListData)(1)
            data.length = 0
            data.capacity = 4
            data.items = gc_alloc(T)(4)
            return _ListImpl.__lift__(data)

    return _ListImpl

# Usage
my_list = List[i32]()
```

## @blue.metafunc (Operator Overloading)

Metafunctions inspect argument types at compile-time and return appropriate implementations:
```spy
from operator import OpSpec

@blue.metafunc
def myprint(m_x):
    if m_x.static_type == int:
        def myprint_int(x: int) -> None:
            print(x)
        return OpSpec(myprint_int)

    if m_x.static_type == str:
        def myprint_str(x: str) -> None:
            print(x)
        return OpSpec(myprint_str)

    raise TypeError("don't know how to print this")

# Usage
myprint(42)       # Calls myprint_int
myprint("hello")  # Calls myprint_str
```

**Key Points:**
- Metafunc parameters are prefixed with `m_` (e.g., `m_x`)
- Access type with `m_x.static_type`
- Must return `OpSpec(implementation_function)`
- Use `OpSpec.NULL` to signal no match

## @typelift (Type Lifting)

Type lifting creates high-level types backed by low-level representations:
```spy
from unsafe import gc_alloc, ptr

@blue.generic
def array(DTYPE, NDIM):
    if NDIM == 1:
        return _array1[DTYPE]
    raise StaticError("unsupported dimension")

@blue.generic
def _array1(DTYPE):
    @struct
    class ArrayData:
        l: i32
        items: ptr[DTYPE]

    @typelift
    class ndarray:
        __ll__: ptr[ArrayData]  # Low-level representation

        def __new__(l: i32) -> ndarray:
            data = gc_alloc(ArrayData)(1)
            data.l = l
            data.items = gc_alloc(DTYPE)(l)
            return ndarray.__lift__(data)

        def __getitem__(self: ndarray, i: i32) -> DTYPE:
            ll = self.__ll__
            if i >= ll.l:
                raise IndexError
            return ll.items[i]

        def __setitem__(self: ndarray, i: i32, v: DTYPE) -> None:
            ll = self.__ll__
            if i >= ll.l:
                raise IndexError
            ll.items[i] = v

    return ndarray

# Usage
arr = array[i32, 1](10)
arr[0] = 42
value = arr[0]
```

**Key Points:**
- `__ll__` field holds the low-level representation
- Use `TypeName.__lift__(low_level_value)` to create instances
- Access low-level value via `instance.__ll__`

## Control Flow

### If Statements
```spy
if x > 0:
    return x
else:
    return -x
```

### While Loops
```spy
i = 0
while i < 10:
    print(i)
    i = i + 1
```

### For Loops:
You need to import `range` explicitly:
```spy
from _range import range

for i in range(10):
    print(i)
```

**IMPORTANT**: when in doubt, prefer using `for i in range(...)` over the equivalent `while`.

## Modules & Imports

### Importing
```spy
from unsafe import gc_alloc, ptr
from math import sqrt, tan
from _list import List
```

### Module Structure
- Standard library in `stdlib/*.spy`
- Import from other `.spy` files

## Error Handling

### Exceptions
```spy
# Raising exceptions
if index >= length:
    raise IndexError

if condition:
    raise ValueError

# Common exceptions: IndexError, ValueError, TypeError, StaticError
```

### StaticError
Used for compile-time errors:
```spy
@blue.generic
def array(DTYPE, NDIM):
    if NDIM == 1:
        return _array1[DTYPE]
    raise StaticError("number of dimensions not supported")
```

## Common Patterns

### Dynamic Array Pattern
See `stdlib/_list.spy` for full implementation:
```spy
@blue.generic
def List(T):
    @struct
    class ListData:
        length: i32
        capacity: i32
        items: ptr[T]

    @typelift
    class _ListImpl:
        __ll__: ptr[ListData]

        def append(self: _ListImpl, item: T) -> None:
            ll = self.__ll__
            if ll.length >= ll.capacity:
                # Grow array
                new_capacity = ll.capacity * 2
                new_items = gc_alloc(T)(new_capacity)
                i = 0
                while i < ll.length:
                    new_items[i] = ll.items[i]
                    i = i + 1
                ll.items = new_items
                ll.capacity = new_capacity
            ll.items[ll.length] = item
            ll.length = ll.length + 1

    return _ListImpl
```

### Tagged Union Pattern
```spy
@struct
class Object:
    obj_type: i32  # 0 = sphere, 1 = plane
    sphere: Sphere
    plane: Plane

def object_intersect(obj: Object, ray: Ray) -> HitRecord:
    if obj.obj_type == 0:
        return sphere_intersect(obj.sphere, ray)
    else:
        return plane_intersect(obj.plane, ray)
```

## Current Limitations

These features are **not yet implemented** but planned for the future:

1. **Arbitrary-dimensional arrays**: Currently hardcoded for 1D, 2D, 3D
3. **Shape attribute for arrays**: No `.shape` property yet
4. **Advanced operator overloading**: Limited metafunc support
5. **Slicing**: No slice syntax support
6. **String formatting**: You need to use "+" between strings
7. **List comprehensions**: Not supported
8. **Lambda expressions**: Not supported
9. **Classes with inheritance**: No inheritance support
10. **Variadic functions**: Limited support through metafunctions
11. **Default arguments**: Not supported
12. **Keyword arguments**: Not supported
13. **Multiple return values**: no support for tuples, use a struct.
14. **Print arguments**: `print` takes only one argument

## Struct field name scoping bug

Due to a bug in the compiler, inside struct methods you cannot use local
variables which have the same name of a field of the struct:

```
@struct
class Point:
    x: i32
    y: i32

    def foo(self: Point) -> i32:
        x = self.x      # <<<< this causes a compiler crash, use a different name
        return x + 1
```


## Best Practices

1. **Use explicit types**: Always annotate function signatures
2. **Prefer stack structs for small data**: Faster than heap allocation
3. **Use pointers for mutable structs**: Stack structs are immutable
4. **Check pointer validity**: Test against NULL before dereferencing
5. **Avoid redeclaration**: Don't redeclare variables in blue functions
6. **Use generics for reusable code**: Leverage `@blue.generic` for type-safe abstractions
7. **Metafunctions for polymorphism**: Use `@blue.metafunc` for operator overloading
8. **Index bounds checking**: Always validate indices for unsafe arrays
9. **Prefer `range()` over `while` for iteration**: Use `for i in range(...)` instead of manual `while` loops - it's more readable and compiles to equally efficient C code

## Common SPy Idioms

### Creating a simple function
```spy
def add(x: i32, y: i32) -> i32:
    return x + y
```

### Working with structs
```spy
# Stack-allocated (immutable)
@struct
class Point:
    x: i32
    y: i32

p = Point(3, 4)
sum = p.x + p.y

# Heap-allocated (mutable)
from unsafe import gc_alloc, ptr

p = gc_alloc(Point)(1)
p.x = 3
p.y = 4
```

### Building a generic data structure
```spy
@blue.generic
def Container(T):
    @typelift
    class _Container:
        __ll__: ptr[T]

        def __new__(value: T) -> _Container:
            data = gc_alloc(T)(1)
            data[0] = value
            return _Container.__lift__(data)

        def get(self: _Container) -> T:
            return self.__ll__[0]

    return _Container

# Usage
int_container = Container[i32](42)
str_container = Container[str]("hello")
```

### Type-based dispatch
```spy
from operator import OpSpec

@blue.metafunc
def process(m_value):
    if m_value.static_type == i32:
        def process_int(value: i32) -> str:
            return "Integer: " + str(value)
        return OpSpec(process_int)

    if m_value.static_type == str:
        def process_str(value: str) -> str:
            return "String: " + value
        return OpSpec(process_str)

    return OpSpec.NULL
```
