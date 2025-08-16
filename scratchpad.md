python -c "import bz2; print(bz2.__doc__)"

python -c "import sys; print('hello')"

## lessons learned


1. brew install coreutils and maybe gcc does not get installed into homebrew bin; 

must link or add Cellar to path
```bash
export PATH="/home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/x86_64-pc-linux-gnu/bin:$PATH"
ln -s /home/linuxbrew/.linuxbrew/Cellar/binutils/2.45/bin/ld /home/linuxbrew/.linuxbrew/bin/ld
ln -s /home/linuxbrew/.linuxbrew/bin/gcc-13 /home/linuxbrew/.linuxbrew/bin/gcc
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
