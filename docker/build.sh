#!/bin/bash
neurodocker generate docker \
	    --pkg-manager apt \
	    --install sudo \
	    -b neurodebian:bullseye \
	    -r "echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers" \
	    -r "useradd -m insight && echo 'insight:insight' | chpasswd && adduser insight sudo" \
	    --ants version=2.3.1 \
	    --dcm2niix method=source version=v1.0.20211006 \
	    --fsl method=binaries version=6.0.3 \
	    --miniconda version=latest use_env=base conda_install="nipype notebook six pyyaml" \
	    	    --user insight \
	    > Dockerfile
docker build --tag insightfsl - < Dockerfile
