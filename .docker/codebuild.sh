#!/bin/bash


# CODEBUILD_WEBHOOK_TRIGGER: branch/<branch_name>, tag/<tag_name>, pr/<pr_number>
if [ ! -z $CODEBUILD_WEBHOOK_TRIGGER ]; then
    WEBHOOK_TYPE=$(echo $CODEBUILD_WEBHOOK_TRIGGER | cut -d '/' -f1)
    NAME=$(echo $CODEBUILD_WEBHOOK_TRIGGER | cut -d '/' -f2-)

    if [ $WEBHOOK_TYPE = "branch" ]; then
        export PUSH=true
        if [ $NAME = "master" ]; then
            export DOCKER_TAG=prod
            export CACHE_DOCKER_TAG=prod
        else
            # Docker tag에 /가 들어갈 수 없어서 -로 변경
            export DOCKER_TAG=$(echo $NAME | sed -e "s/\//-/g")
            export CACHE_DOCKER_TAG=dev
        fi
    elif [ $WEBHOOK_TYPE = "tag" ]; then
        export PUSH=true
        export DOCKER_TAG=$NAME
        export CACHE_DOCKER_TAG=prod
    else # pr
        export PUSH=false
        export CACHE_DOCKER_TAG=dev
    fi
else  # 직접 codebuild 실행
    export PUSH=false
    export CACHE_DOCKER_TAG=dev
fi

echo $WEBHOOK_TYPE $CACHE_DOCKER_TAG $DOCKER_TAG $PUSH
