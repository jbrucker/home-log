#!/bin/bash

activate_venv() {
	DIR=$( dirname "${BASH_SOURCE[0]}")
	ENVDIR="$DIR/env"
	echo "Activate virtual env in $ENVDIR"
	. $ENVDIR/bin/activate
}

if [[ ! -v VIRTUAL_ENV ]]; then
	activate_venv
fi
uvicorn app.main:app --reload
