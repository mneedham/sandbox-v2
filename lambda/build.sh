#!/bin/bash
cp -R SandboxLambdaLibrary/* SandboxGetRunningInstancesForUser/
cp -R SandboxLambdaLibrary/* SandboxRunInstance/
cp -R SandboxLambdaLibrary/* Auth0JwtAuthorizor/
cp -R SandboxLambdaLibrary/* SandboxMaintainInstances/
cp -R SandboxLambdaLibrary/* SandboxRetrieveUserLogs/
cp -R SandboxLambdaLibrary/* SandboxGetUsecases/
cp -R SandboxLambdaLibrary/* SandboxSendEmails/
cp -R SandboxLambdaLibrary/* SandboxGetInstanceByHashKey/
cp -R SandboxLambdaLibrary/* SandboxStopInstance/
cp -R SandboxLambdaLibrary/* SandboxBackupInstance/

./makeZips.sh
