#export SPY_ROOT=$(python -c 'import spy; print(spy.ROOT)')

rm -rf build
rm -f _sobel_spy.c
rm -f _sobel_spy.*.so
~/anaconda/spy/venv/bin/spy --cwrite sobel.spy || exit
python setup.py build_ext -if
