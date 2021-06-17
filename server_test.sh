#!/bin/bash

for i in {1..10000}
do
   echo ${i}
   curl localhost:5000/sleep &1>/dev/null &2>/dev/null &0>/dev/null &
done
