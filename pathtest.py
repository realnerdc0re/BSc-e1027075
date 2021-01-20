#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path, PureWindowsPath
import os



if __name__ == '__main__':


	# get current working directory
	wd = Path.cwd()
	print(wd)

	# windows base drive
	wwd = Path("C:")
	print(wwd)

	# get current users home directory
	hd = Path.home()
	print(hd)


	# forge directories

	# dietpi paths
	flowd = wd / 'csv' / 'flow-sampled'
	print(flowd)

	# path conversions
	print(flowd.as_uri())
	print(flowd.as_posix())

	print(PureWindowsPath(flowd)) # misses actual drive prefix, but changes slashes to backslashes
	print(PureWindowsPath(os.path.join("C:",flowd)))