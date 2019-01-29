#!/bin/bash
jobs=( 7033282 7033286 7033287 7033288  7033285 7033284 7033283 7033272 7033276 7033277 7033281);
for i in "${jobs[@]}"
do
    echo $i
    submit --kill $i &
done
