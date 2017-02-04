  const API_PATH = "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod";
  const AUTH_URL = "http://neo4j-sandbox-www-auth.s3-website-us-east-1.amazonaws.com";
  const CODE_SNIPPETS_PATH = "https://s3.amazonaws.com/neo4j-sandbox-code-snippets";
  const AUTH_CLIENT_ID = "CK4MU2kBWYkDXdWcKs5mj0GbgzEDfifL";
  const AUTH_DELEGATION_URL = "https://devrel-test.auth0.com/delegation"

  var pollInterval;
  var usecases = false;
  var runningInstances = false;
  var editors = {};
  var identityName = '';
  var activeUsecases = {}
  var activeInstancesUpdated = false;
  var emailVerificationNotNeeded = false;
  var emailVerified = false;
  var activeInstances = [];

  var listener = function(event) {
    if (event.origin == AUTH_URL) {
      $('.jumbotron').fadeOut("fast");
      $('.marketing').fadeOut("fast");
      $('.btn-login').hide();
      $('.btn-logout').show();
      $('.btn-launch').show();
      //$('#logs').show();
      event.source.close();
      localStorage.setItem('id_token', event.data.token)
      localStorage.setItem('profile', JSON.stringify(event.data.profile))
      localStorage.setItem('access_token', event.data.accessToken)
      localStorage.setItem('refresh_token', event.data.refreshToken)
      show_profile_info(event.data.profile)
      profileObj = event.data.profile

      if (profileObj && 'email_verified' in profileObj && profileObj['email_verified'] == true) {
        emailVerified = true;
      } else if (! ('email_verified' in profileObj)) {
        emailVerficationNotNeeded = true;
      }
      if (emailVerified || emailVerificationNotNeeded) {
        $('.need-verification').hide();
        retrieve_usecases();
        conditional_update_usecases();
        retrieve_update_instances();
      } else {
        updateIdentity();
        updateProfile();
        $('#sandboxListContainer').hide();
        $('#usecaseListContainer').hide();
        $('.need-verification').show();
      }
    }
  }

  var updateIdentity = function() {
    var profile = JSON.parse(localStorage.getItem('profile'));
    if('given_name' in profile) {
      identityName = profile['given_name'];
    } else if('name' in profile) {
      identityName = profile['name'];
    } else if('nickname' in profile) {
      identityName = profile['nickname'];
    } else if('email' in profile) {
      identityName = profile['email'];
    } 
    $('#identityGreeting').text("Greetings " + identityName);
    $('#identityContainer').fadeIn('fast');
  }

  var getTimeDiff = function(time1, time2) {
    var hourDiff = time2 - time1;
    var diffDays = Math.floor(hourDiff / 86400000);
    var diffHrs = Math.floor((hourDiff % 86400000) / 3600000);
    var diffMins = Math.floor(((hourDiff % 86400000) % 3600000) / 60000);
    return {"days": diffDays, "hours": diffHrs, "mins": diffMins};
  }
   
  if (window.addEventListener){
    addEventListener("message", listener, false)
  } else {
    attachEvent("onmessage", listener)
  }

  var shutdownInstanceAction = function(sandboxDiv, instance, clickItem) {
    clickItem.click( function() {
        shutdownInstance(instance.sandboxHashKey, sandboxDiv);
        sandboxDiv.fadeTo(400, 0.3);
        sandboxDiv.attr('style', '-webkit-filter: grayscale(1);');
    });
  }

  var backupInstanceAction = function(sandboxDiv, instance, clickItem) {
    clickItem.click( function() {
        backupInstance(instance.sandboxHashKey, sandboxDiv);
        //sandboxDiv.fadeTo(400, 0.3);
        //sandboxDiv.attr('style', '-webkit-filter: grayscale(1);');
    });
  }

  var loginButtonAction = function(e) {
    $('.btn-login').hide();
    win = window.open(AUTH_URL + "/",
                "loginWindow",
                "location=0,status=0,scrollbars=0, width=1080,height=720");
    try {
      win.moveTo(500, 300);
    } catch (e) {
    }
    if (e.target.dataset && e.target.dataset['usecase']) {
      targetUsecase = e.target.dataset['usecase'];
    } else {
      targetUsecase = null;
    }
    window.addEventListener('message', function(event) {
      clearInterval(pollInterval);
    });
    pollInterval = setInterval(function (e) {
      win.postMessage('Polling for results', 
                      AUTH_URL)
      }, 6000);
  }

  var launchButtonAction = function(button) {
    button.click(function (e) {
      //this.hide();
      //$('.btn-launch').hide();  
      var id_token = localStorage.getItem('id_token');
      if (! id_token) {
        return $('.btn-login').trigger(e);  
      }
      if (e.target.dataset && e.target.dataset['usecase']) {
        // hide panel
        $( this ).closest('.panel').fadeOut('slow');
        // TODO: Be smarter about refreshes - don't need net calls, but can count divs
        // TODO: Rebalance columns
        //$("#modalLaunchInstance").modal();
        return launchInstance(e.target.dataset['usecase']);
      }
    });
  }

  var shutdownInstance = function(sandboxHashKey, sandboxDiv) {
    var id_token = localStorage.getItem('id_token');

    $.ajax
    ({
      type: "POST",
      url: `${API_PATH}/SandboxStopInstance`,
      dataType: 'json',
      data: JSON.stringify({ "sandboxHashKey": sandboxHashKey}),
      contentType: "application/json",
      async: true,
      headers: {
        "Authorization": id_token
      },
      success: function (data){
        sandboxDiv.remove();
        // TODO check number of sandbox divs and update UI based upon it
        updateUx();
      }
    });
  }

  var backupInstance = function(sandboxHashKey, sandboxDiv) {
    var id_token = localStorage.getItem('id_token');

    $.ajax
    ({
      type: "POST",
      url: `${API_PATH}/SandboxBackupInstance`,
      dataType: 'json',
      data: JSON.stringify({ "sandboxHashKey": sandboxHashKey}),
      contentType: "application/json",
      async: true,
      headers: {
        "Authorization": id_token
      },
      success: function (data){
        //sandboxDiv.remove();
        // TODO check number of sandbox divs and update UI based upon it
        updateUx();
      }
    });
  }

  var updateUx = function() {
    activeInstancesUpdated = false;
    activeUsecases = [];
    retrieve_update_instances();
    conditional_update_usecases();
  }

  var launchInstance = function(usecase) {
    var id_token = localStorage.getItem('id_token');

    $.ajax
    ({
      type: "POST",
      url: `${API_PATH}/SandboxRunInstance`,
      dataType: 'json',
      data: JSON.stringify({ "usecase": usecase}),
      contentType: "application/json",
      async: true,
      headers: {
        "Authorization": id_token 
      },
      success: function (data){
        update_instances(data, usecases);
        setTimeout(function() { updateUx() }, 1000);
      }
    });
  }

  var emailVerificationCheck = function() {
    var profile = localStorage.getItem('profile');
    if (profile) {
      profileObj = JSON.parse(profile);
      if ('email_verified' in profileObj && profileObj['email_verified'] == true) {
        emailVerified = true
      } else if (! ('email_verified' in profileObj)) {
        emailVerificationNotNeeded = true;
      }
      if (emailVerified || emailVerificationNotNeeded) {
        $('.need-verification').hide();
        retrieve_usecases();
        retrieve_update_instances();
        conditional_update_usecases();
      }
    }
  }

  var updateProfile = function() {
    var access_token = localStorage.getItem('access_token');
    $.ajax
    ({
      type: "GET",
      url: `https://devrel-test.auth0.com/userinfo`,
      dataType: 'json',
      async: true,
      headers: {
        "Authorization": "Bearer " + access_token
      },
      success: function (data){
       localStorage.setItem('profile', JSON.stringify(data));
       emailVerificationCheck();
      }
    });
  }

  var checkIfInstanceActive = function(sandboxHashKey) {
      var id_token = localStorage.getItem('id_token');
      $.ajax
      ({
        type: "GET",
        url: `${API_PATH}/SandboxGetInstanceByHashKey`,
        data: {"sandboxHashKey": sandboxHashKey, "verifyConnect": "true"},
        dataType: 'text',
        async: true,
        headers: {
          "Authorization": id_token,
          "Cache-Control": "max-age=0" 
        },
        success: function (data){
          activeInstances.push(sandboxHashKey);
        },
        error: function (jqXHR, textStatus, errorThrown) {
          console.log(errorThrown);
        }
      });
  }

  var show_profile_info = function(profile) {
     $('.nickname').text(profile.nickname);
     $('.btn-login').hide();
     $('.avatar').attr('src', profile.picture).show();
     $('.btn-logout').show();
     $('#welcome').show();
  };

  var retrieve_update_instances = function(retry=true) {
    var id_token = localStorage.getItem('id_token');
    if (id_token) {
        $('.btn-login').hide();
        $('.btn-logout').show();
        $('#welcome').show();
        /*
        $('#logs').show();
        var editor = CodeMirror.fromTextArea(document.getElementById('logs'), {
          mode: 'shell',
          lineNumbers: true
        })$a
        */;
        $.ajax
        ({
          type: "GET",
          url: `${API_PATH}/SandboxGetRunningInstancesForUser`,
          dataType: 'json',
          async: true,
          headers: {
            "Authorization": id_token,
            "Cache-Control": "max-age=0" 
          },
          success: function (data){
            runningInstances = data;
            if (usecases) {
              update_instances(data, usecases);
            } else {
              window.setTimeout( 
                function () { check_for_instances_and_usecases(200) }
                ,200);
            }
          },
          error: function (jqXHR, textStatus, errorThrown) {
            /* CORS headers unavailable from AWS API Gateway
               when throwing 401, so status details missing. 
               Assume errors are auth failures. */
              // Refresh token
            if (retry) {
              $.ajax
              ({
                type: "POST",
                url: AUTH_DELEGATION_URL,
                contentType: "application/json",
                dataType: 'json',
                async: true,
                data: JSON.stringify(
                  { "client_id": AUTH_CLIENT_ID,
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "refresh_token": localStorage.getItem('refresh_token'),
                    "api_type": "app" }),
                success: function (data){
                  localStorage.setItem('id_token', data.id_token);
                  retrieve_update_instances(false);
                }
              });
            }
          }
        });
        //retrieve_logs(editor, null);
        //$('.btn-launch').show();
    }
  }

  var check_for_instances_and_usecases = function(time) {
    if (runningInstances && usecases) {
      update_instances(runningInstances, usecases);
    } else {
      console.log('Timeout setting for: ' + (time * 2));
      window.setTimeout( 
              function () { check_for_instances_and_usecases(time*2) }
              ,time * 2);
    }
  }

  var retrieve_usecases = function() {
    $.ajax
    ({
      type: "GET",
      url: `${API_PATH}/SandboxGetUsecases`,
      dataType: 'json',
      async: true,
      headers: {
      },
      success: function (data){
        usecases = data;
      }
    });
  }

  var retrieve_show_code_snippets = function(usecase, username, password, ip, httpPort, boltPort, tabjq) {
    tabjq.attr('style', 'min-height: 400px');
    var languages = ['php', 'py', 'java', 'js'];
    var tabs = tabjq.tabs({heightStyle: "content", activate: function() {codeTabActivate(usecase, language)}}).css({'min-height':'300px'});
    for (var langId in languages) {
      language = languages[langId];
      (function(language, usecase, username, password, ip, httpPort, boltPort, tabjq) {
        $.ajax
        ({
          type: "GET",
          url: `${CODE_SNIPPETS_PATH}/${usecase}.${language}.txt`,
          dataType: 'text',
          async: true,
          headers: {
          },
          success: function (data) {
              var ul = tabs.find( "ul" );
              tabs.on( "tabscreate", function( event, ui ) {codeTabActivate(usecase, language);} );
              var code = data.replace("<USERNAME>", username)
                .replace("<PASSWORD>", password)
                .replace("<HOST>", ip)
                .replace("<HTTPPORT>", httpPort)
                .replace("<BOLTPORT>", boltPort)
              $( `<li><a href="#tab-code-${language}">${language}</a></li>` ).appendTo( ul );
              var div = $( `<div id="tab-code-${language}"/ >`);
              var textarea = $('<textarea/>')
              .attr('class', 'code-textarea')
              .attr('style', 'min-height: 200px; max-height: 300px; width: 100%;')
              .text(code)
              .appendTo(div);
              div.appendTo( tabs );
              var mode = 'clike';
              if (language == 'py') {
                mode = 'text/x-cython';
              } else if (language == 'java') {
                mode = 'text/x-java';
              } else if (language == 'js') {
                mode = 'text/javascript';
              } else if (language == 'php') {
                mode = 'application/x-httpd-php';
              }
              editors[usecase + '-' + language] = CodeMirror.fromTextArea(textarea.get()[0], {mode: 'javascript', autoRefresh: true, theme: "paraiso-dark"})

/*
              var editor = CodeMirror.fromTextArea(
                  textarea[0], {
                  mode: 'shell',
                  lineNumbers: true
              });
*/
              //$('.ui-tabs').tabs( "option", "active", 0 );
              tabs.tabs("refresh"); 
              tabs.tabs('option', 'active', 0); 
              //$( "#tabs" ).tabs( "refresh" );
              //$( "#accordion" ).accordion( "refresh" );
              /* tabs.tabs({
                active: 0,
                activate: codeTabActivate(usecase, language)
                }).css({'resize':'none','min-height':'300px'}); */
          }
        });
      })(language, usecase, username, password, ip, httpPort, boltPort, tabjq);
    }
  }

  var codeTabActivate = function(usecase, language) {
    return function(event, ui) {
      editors[usecase + '-' + language].refresh();
      //$( "#tabs" ).tabs( "refresh" );
      //$( "#accordion" ).accordion( "refresh" );
    }
  }

  var retrieve_logs = function(editor, sbid, nextToken) {
    var id_token = localStorage.getItem('id_token');
    if (id_token) {
      data = {"sbid": sbid}
      if (nextToken) {
        data['nextToken'] = nextToken
      }
      $.ajax
      ({
        type: "GET",
        url: `${API_PATH}/SandboxRetrieveUserLogs`,
        data: data,
        dataType: 'json',
        async: true,
        headers: {
          "Authorization": id_token
        },
        success: function (data){
          display_logs(data, editor);
        }
      });
    } else {
      return False;
    }
  }

  var display_logs = function(data, editor) {
    for (var eventid in data.events) {
      editor.replaceRange(data.events[eventid].message + "\n", CodeMirror.Pos(editor.lastLine()));
    }
/*    if (data.nextForwardToken) {
      setTimeout(retrieve_logs, 10000, editor, data.nextForwardToken);
    }*/
  } 


  var conditional_update_usecases = function() {
    if (usecases && activeInstancesUpdated) {
      update_usecases(usecases);
    } else {
      setTimeout(function() { conditional_update_usecases() }, 100); 
    }
  }

  var update_usecases = function(usecases) {
    availableForLaunchCount = 0;
    $('#usecaseList').find('.col-md-4').empty();
    for (var usecaseNum in usecases) {
      usecase = usecases[usecaseNum]
      ucname = usecase.name

      /* always show blank sandbox for testing TODO remove */
      if (! (ucname in activeUsecases)) {
        columnNum = (availableForLaunchCount % 3 ) + 1;
        panelDiv = $('<div/>').attr('class', 'panel panel-primary')
          .append(
            $('<div/>').attr('class', 'panel-heading').text(usecase.long_name)
          )
          .append(
            $('<div/>').attr('class', 'panel-body')
              .append(
                $('<button/>').attr('type','button').attr('class','btn btn-success btn-launch')
                .attr('data-usecase', ucname)
                .text('Launch Sandbox')
              )
          );
        $(".uc-col-" + columnNum).append(panelDiv);
        launchButtonAction(panelDiv.find('.btn-launch'));
        availableForLaunchCount++;
      }
    }
    $("#usecaseListContainer").show();
    if (availableForLaunchCount > 0) {
      $('#usecaseListAlert').hide();
    } else {
      $('#usecaseListAlert').show();
    }
  }

  var update_instances = function(instances, usecases) {
    console.log(instances);
    console.log(usecases);


    sandboxListDiv = $("#sandboxList");

    // this is a new launch
    if (! Array.isArray(instances) ){
      instances = [ instances ];
    }

    var shouldUpdateInstances = false;


    for (var instanceNum in instances) {
      var instance = instances[instanceNum]
      instance.username = 'neo4j';

      activeUsecases[instance.usecase] = true;

      for (var ucNum in usecases) {
        if (usecases[ucNum].name == instance.usecase) {
          thisUsecase = usecases[ucNum]
        }
      }

      existingSandbox = sandboxListDiv.find(`[data-sandboxhashkey='${instance.sandboxHashKey}']`);
      if ('status' in instance && instance['status'] == 'PENDING') {
        sandboxDiv = $("#sandbox_launching_template").clone();
      } else {
        sandboxDiv = $("#sandbox_template").clone();
      }
      sandboxDiv
      .removeAttr('id')
      .attr('data-sandboxid', instance.sandboxId)
      .attr('data-sandboxhashkey', instance.sandboxHashKey);
      sandboxDiv.find('.navbar-brand').text(thisUsecase.long_name);

      sandboxDiv.find('.connection a').click(update_sandbox_panel('connection', instance.sandboxId));
      var connectionDiv = sandboxDiv.find('.panel-body-content').find('.connection');
      connectionDiv.empty();
      dateDiff = getTimeDiff(Date.now(), instance.expires);
      if (dateDiff['days'] == 1) {
        daysStr = 'day';
      } else {
        daysStr = 'days';
      }
      if (dateDiff['minutes'] == 1) {
        minsStr = 'minute';
      } else {
        minsStr = 'minutes';
      }
      if (dateDiff['hours'] == 1) {
        hoursStr = 'minute';
      } else {
        hoursStr = 'hours';
      }
      expiresString = `${dateDiff['days']} ${daysStr}, ${dateDiff['hours']} ${hoursStr}, ${dateDiff['mins']} ${minsStr}`
      triggerExpiresWarning = false;
      expiresWarningLevel = '';
      if (dateDiff['days'] < 3) {
        triggerExpiresWarning = true;
        if (dateDiff['days'] < 1) {
          expiresWarningLevel = 'danger';
        } else {
          expiresWarningLevel = 'warning';
        }
        sandboxDiv.find('.panel-body-alerts').append($('<div/>').attr('class', `alert alert-custom alert-${expiresWarningLevel}`).html(`<strong>Warning:</strong> Sandbox expires in ${expiresString}. <button type="button" class="btn btn-primary btn-sm" data-toggle="modal" data-target="#modalExtendSandbox">Extend Sandbox</button>`));
        //$(".extend-sandbox").on("click", function() { $("#extend-sandbox-dialog").dialog("open") });
      }

      if ('status' in instance && instance['status'] == 'PENDING') {
        newLaunch = true;
        connectionDiv.append($('<p/>').text('Launching! Will show connection info when available.'));
        shouldUpdateInstances = true;
      } else if (instance.ip == null) {
        newLaunch = false;
        connectionDiv.append($('<p/>').text('Launching! Will show connection info when available.'));
        shouldUpdateInstances = true;
      } else if ((instance['connectionVerified'] != true) && $.inArray(instance.sandboxHashKey,activeInstances) == -1){
        newLaunch = false;
        connectionDiv.append($('<p/>').text('Connecting to sandbox.'));
        checkIfInstanceActive(instance.sandboxHashKey);
        shouldUpdateInstances = true;
      } else {
        newLaunch = false;
        connectionDiv.append(
              $('<img/>')
                .attr('src', thisUsecase['logo'])
                .attr('height', '175')
                .attr('style', 'float: left; margin-right: 5px;')
        );
        connectionDiv.append(
            $('<p/>')
              .append(
                $('<b/>').text('Neo4j Browser: '))
              .append(
                $('<b/>')
                .append($('<a/>')
                  .attr('href', `http://${instance.ip}:${instance.port}/`)
                  .attr('target', '_blank')
                  .text(`http://${instance.ip}:${instance.port}/`)
              )))
            .append($('<p/>')
              .html(`<b>Username:</b> ${instance.username}<br />` +
                    //`<b>Password:</b> <input type="text" size="${instance.password.length}" id="pw-${instance.sandboxHashKey}" value="${instance.password}" style="border: 0px"></input>` +
                    `<b>Password:</b> <span id="pw-${instance.sandboxHashKey}" style="margin-right: 10px">${instance.password}</span>` +
                    `<button type="button" class="btn copybtn btn-default btn-xs" data-clipboard-target="#pw-${instance.sandboxHashKey}">` + 
                    `<span class="glyphicon glyphicon-copy" aria-hidden="true"></span></button>` +
                    `` ))
            .append($('<p/>')
              .html(`<b>IP Address:</b> ${instance.ip}<br />` +
                    `<b>HTTP Port:</b> ${instance.port}<br />` +
                    `<b>Bolt Port:</b> ${instance.boltPort}`))
            .append($('<p/>')
              .html(`<b>Expires:</b> ${expiresString}`));
      }

      sandboxDiv.find('.datamodel a').click(update_sandbox_panel('datamodel', instance.sandboxId));
      var datamodelDiv = sandboxDiv.find('.panel-body-content').find('.datamodel');
      datamodelDiv.empty().append($('<img/>')
                          .attr('src', instance.modelImage)
                          .attr('width', '100%'));


      sandboxDiv.find('.code a').click(update_sandbox_panel('code', instance.sandboxId));
      var codeDiv = sandboxDiv.find('.panel-body-content').find('.code');
      codeDiv.empty().append($('<div/>')
                          .attr('class', `tabs-code-${instance.usecase} tabs-nohdr`)
                          .append($('<ul />')))
                        .tabs({heightStyle: "content"});// .tabs("refresh");
      retrieve_show_code_snippets(instance.usecase, instance.username, instance.password, instance.ip, instance.port, instance.boltPort, codeDiv.find(`.tabs-code-${instance.usecase}`));

      shutdownInstanceAction(sandboxDiv, instance, sandboxDiv.find('.shutdown a') );
      backupInstanceAction(sandboxDiv, instance, sandboxDiv.find('.backup a') );
      sandboxDiv.hide();
      if (existingSandbox.length == 0) {
        sandboxListDiv.append(sandboxDiv);
      } else {
        // sandbox already here, update as necessary
        existingSandbox.replaceWith(sandboxDiv);
      }
      if (newLaunch) {
        sandboxDiv.fadeIn(2000);
      } else {
        sandboxDiv.show();
      }
    }

    if (instances.length > 0) {
      $("#sandboxListContainer").show();
    }

    if (shouldUpdateInstances) {
        setTimeout(function() { retrieve_update_instances() }, 2000);
    }

    activeInstancesUpdated = true;
  }

  var update_sandbox_panel = function(panelName, sandboxId) {
    return function (event) {
        if (! event.target.parentElement.classList.contains('active')) {
            // this element isn't active, set it active and update content
            $( event.target.parentElement.parentElement ).find('li').removeClass('active');
            $( event.target.parentElement ).addClass('active');
            $( event.target ).closest('.panel').find('.panel-body-content').children().hide();
            $( event.target ).closest('.panel').find('.panel-body-content').find('.' + panelName).show();
           console.log('Selected ' + panelName + ' for sandbox id: ' + sandboxId);
        }
    }
  }

  var show_instances = function(instances) {
    for (var instanceNum in instances) {
        var e = jQuery.Event('runningInstance');
        e.usecase = instances[instanceNum].usecase;
        if(instances[instanceNum].ip) {
          window.dispatchEvent(new CustomEvent('runningInstance', {detail: { usecase: instances[instanceNum].usecase, modelImage: instances[instanceNum].modelImage, sandboxId: instances[instanceNum].sandboxId, ip: instances[instanceNum].ip, boltPort: instances[instanceNum].boltPort, port: instances[instanceNum].port, username: 'neo4j', password: instances[instanceNum].password, taskId: instances[instanceNum].taskid }}));
        } else {
          window.dispatchEvent(new CustomEvent('startingInstance', {detail: { usecase: instances[instanceNum].usecase, sandboxId: instances[instanceNum].sandboxId } }));
          //setTimeout(retrieve_show_instances, 5000);
        }
    }
  }

  var logout = function() {
    localStorage.removeItem('id_token');
    localStorage.removeItem('profile');
    localStorage.removeItem('access_token');
    $('.btn-logout').hide();
    $('.btn-login').show();
    $('.marketing').show();
    $('.jumbotron').show();
    $('#sandboxList').empty();
    $('#sandboxListContainer').hide();
    $('#usecaseListContainer').hide();
    $('#identityContainer').hide();
    window.location.href = window.location.href;
  };

$(document).ready(function() {
  $('.btn-login').click(function (e) {
    loginButtonAction(e);
  });
  $('.btn-startnow').click(function (e) {
    loginButtonAction(e);
  });
  $('.btn-logout').click(function(e) {
    e.preventDefault();
    logout();
  })
  new Clipboard('.copybtn');
  var profile = localStorage.getItem('profile');
  if (profile) {
    profileObj = JSON.parse(profile);
    show_profile_info(profileObj);
    if ('email_verified' in profileObj && profileObj['email_verified'] == false) {
      emailVerified = false;
    } else if (! ('email_verified' in profileObj)) {
      emailVerificationNotNeeded = true;
    }
    $('.jumbotron').fadeOut("fast");
    $('.marketing').fadeOut("fast");
    $('.btn-login').hide();
    $('.btn-logout').show();
    if ( (!emailVerified) && (!emailVerificationNotNeeded) ) {
      updateProfile();
      $('#sandboxListContainer').hide();
      $('#usecaseListContainer').hide();
      $('.need-verification').show();
    }
    if (localStorage.getItem('id_token')) {
      // TODO FIGURE OUT WHY DOUBLE LOADING
      updateIdentity();
      emailVerificationCheck();
    }
  }
});

