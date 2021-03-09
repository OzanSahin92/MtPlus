#!/bin/bash

for i in 2 8 16; do 
	scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/spatiallyReducedES/0_95.0_num_of_events_subseas.taumax"${i}".4dx4dy.ndjfm.spatiallyReduced.txt Data/ES_taumax"${i}"_spatially_reduced/
	scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/spatiallyReducedES/0_95.0_thresh_subseas.taumax"${i}".4dx4dy.ndjfm.spatiallyReduced.txt Data/ES_taumax"${i}"_spatially_reduced/
	j=99													
	for ((n=0; n<=j; n++)); do															
		scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/spatiallyReducedES/"${n}"_95.0_es_subseas.taumax"${i}".4dx4dy.ndjfm.spatiallyReduced.txt.npz Data/ES_taumax"${i}"_spatially_reduced/
		scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/spatiallyReducedES/"${n}"_95.0_sign_es_subseas.taumax"${i}".4dx4dy.ndjfm.spatiallyReduced.txt.npz Data/ES_taumax"${i}"_spatially_reduced/
	done
done 

