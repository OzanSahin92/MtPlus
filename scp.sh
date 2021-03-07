#!/bin/bash


for i in 2 8 16; do #4 6 10 12 14  
	scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/final_es995/final_es9950num_of_events_subseas.taumax"${i}".4dx4dy.ndjfm.txt /atm_glomod/user/osahin/data/ERA5/daymean_1979-2019/NDJFM/ES_taumax"${i}"_subseas/
	scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/final_es995/final_es9950thresh_subseas.taumax"${i}".4dx4dy.ndjfm.txt /atm_glomod/user/osahin/data/ERA5/daymean_1979-2019/NDJFM/ES_taumax"${i}"_subseas/
	j=99													
	for ((n=0; n<=j; n++)); do															#erstellt in diesen Ordnern die Ordner 01, 02 usw.
		scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/final_es995/final_es995"${n}"es_subseas.taumax"${i}".4dx4dy.ndjfm.txt.npz /atm_glomod/user/osahin/data/ERA5/daymean_1979-2019/NDJFM/ES_taumax"${i}"_subseas/
		scp sahin@cluster.pik-potsdam.de:/p/tmp/sahin/final_es995/final_es995"${n}"sign_es_subseas.taumax"${i}".4dx4dy.ndjfm.txt.npz /atm_glomod/user/osahin/data/ERA5/daymean_1979-2019/NDJFM/ES_taumax"${i}"_subseas/
	done
done 

