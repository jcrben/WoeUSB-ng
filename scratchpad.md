python -c "import bz2; print(bz2.__doc__)"

python -c "import sys; print('hello')"

## tkinter support
`brew install python-tk@3.13`
OR
https://github.com/jdx/mise/issues/2189#issuecomment-2212359376

see also: https://github.com/pyenv/pyenv/issues/3116#issuecomment-2511938813

```
brew install tcl-tk@8
export TCL_LIBRARY=$(brew --prefix tcl-tk)/lib; export TK_LIBRARY=$(brew --prefix tcl-tk)/lib
mise uninstall python@3.12.3
mise install python@3.12.3
# open a new shell to get rid of environment variables and run:
python -m tkinter
# which should open the Tcl/Tk test window
```

## tldr
`pip install --only-binary=all --no-cache-dir --force-reinstall wxPython`

```bash
pip install setuptools
python setup.py develop
```
## brew deps

```bash
brew install binutils
brew install bzip2
brew install gcc@13
brew install krb5 libx11 libxext libxrender libxrandr libxfixes libxcursor libxinerama libxi bzip2 openssl@3 curl
brew install gtk+3 pkg-config
```

## lessons learned

1. brew install coreutils and maybe gcc does not get installed into homebrew bin; 

must link or add Cellar to path
```bash
export PATH="/home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/x86_64-pc-linux-gnu/bin:$PATH"
ln -s /home/linuxbrew/.linuxbrew/bin/gcc-13 /home/linuxbrew/.linuxbrew/bin/gcc

# either export path - DOES NOT WORK
# ~~export PATH=/home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin:"$PATH"~~
# OR link:
ln -s /home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin/ld /home/linuxbrew/.linuxbrew/bin/ld
ln -s /home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin/ar /home/linuxbrew/.linuxbrew/bin/ar
# ...need more
cd /home/linuxbrew/.linuxbrew/bin && for tool in addr2line ar as c++filt coffdump dlltool dllwrap elfedit gprof gprofng gprofng-archive gprofng-collect-app gprofng-display-html gprofng-display-src gprofng-display-text ld ld.bfd nm objcopy objdump ranlib readelf size srconv strings strip sysdump windmc windres; do ln -sf /home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin/$tool $tool; done
```

2. don't mix system and homebrew dependencies

sticking to just homebrew...

export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

3. to fix importing c-based python libs like _bz2 do:

```bash
export LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib
python -c "import _bz2; print('_bz2 module imported successfully')"
```

4. python clears build dir by default, `pip install -e . --no-clean` keeps it

5. can use `pkg-config <lib-name> --libs` - for example `pkg-config gtk+-3.0 --libs` - to get the libs. To put them in the LD_LIBRARY_PATH need to transform them tho: `pkg-config gtk+-3.0 --libs | tr ' ' '\n' | grep '^-L' | sed 's/^-L//' | paste -sd: -`

something like:
`export LD_LIBRARY_PATH="$(pkg-config gtk+-3.0 --libs | tr ' ' '\n' | grep '^-L' | sed 's/^-L//' | paste -sd: -):$LD_LIBRARY_PATH"`

6. wxPython has a bunch of prebuilt wheels at https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
