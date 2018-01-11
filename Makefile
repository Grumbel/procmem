# procmem - A process memory inspection tool
# Copyright (C) 2018 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

SOURCES := $(wildcard \
  procmem/*.py \
  tests/*.py)

all: mypy flake test # autopep

autopep:
	autopep8  --max-line=120  --in-place $(SOURCES)

test:
	python3 -m unittest discover -s tests/

mypy:
	mypy --ignore-missing-imports $(SOURCES)

flake:
	flake8 --ignore=N802 --max-line-length=120 $(SOURCES)

PYLINT_TARGETS := $(addprefix .pylint/, $(SOURCES))

$(PYLINT_TARGETS): .pylint/%.py: %.py
	mkdir -p $(dir $@)
	PYTHONPATH=. epylint3 $< --rcfile=.pylintrc --max-line-length=120
	touch $@

pylint: $(PYLINT_TARGETS)

clean:
	rm -vrf .pylint/

install:
	sudo -H pip3 install --force-reinstall --ignore-installed --no-deps .

.PHONY: all autopep flake test mypy flake pylint clean install

# EOF #
