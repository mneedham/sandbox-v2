#!/bin/bash
cd SandboxGetRunningInstancesForUser
zip -r9 ../SandboxGetRunningInstancesForUser.zip *
cd ..
cd SandboxRunInstance
zip -r9 ../SandboxRunInstance.zip *
cd ..
cd Auth0JwtAuthorizor
zip -r9 ../Auth0JwtAuthorizor.zip *
cd ..
cd SandboxMaintainInstances
zip -r9 ../SandboxMaintainInstances.zip *
cd ..
cd SandboxRetrieveUserLogs
zip -r9 ../SandboxRetrieveUserLogs.zip *
cd ..
