#!/usr/bin/bash

#uvicorn src.main:app --reload --host 127.0.0.1 --log-config ./log.ini #192.168.1.142 


uvicorn src.main:app --reload --host 127.0.0.1 --log-config ./log.ini
