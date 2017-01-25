  const API_PATH = "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod";
  const AUTH_URL = "https://auth.neo4j.com/index.html";
  const CODE_SNIPPETS_PATH = "https://s3.amazonaws.com/neo4j-sandbox-code-snippets";

  var pollInterval;
  var usecases = false;
  var runningInstances = false;
  var editors = {};

  var listener = function(event) {
    if (event.origin == "https://auth.neo4j.com") {
      $('.jumbotron').hide();
      $('.marketing').hide();
      $('.btn-launch').show();
      //$('#logs').show();
      event.source.close();
      localStorage.setItem('id_token', event.data.token)
      localStorage.setItem('profile', JSON.stringify(event.data.profile))
      show_profile_info(event.data.profile)
      retrieve_update_instances();
    }
  }
   
  if (window.addEventListener){
    addEventListener("message", listener, false)
  } else {
    attachEvent("onmessage", listener)
  }

  var loginButtonAction = function(e) {
    $('.btn-login').hide();
    win = window.open(AUTH_URL,
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
      if (targetUsecase) {
        window.setTimeout(launchInstance(targetUsecase), 1000);
      }
    });
    pollInterval = setInterval(function (e) {
      win.postMessage('Polling for results', 
                      AUTH_URL)
      }, 6000);
  }

  var launchButtonAction = function() {
    $('.btn-launch').click(function (e) {
      //this.hide();
      //$('.btn-launch').hide();  
      var id_token = localStorage.getItem('id_token');
      if (! id_token) {
        return $('.btn-login').trigger(e);  
      }
      if (e.target.dataset && e.target.dataset['usecase']) {
        // hide panel
        $( this ).closest('.panel').hide();
        // TODO: Rebalance columns
        return launchInstance(e.target.dataset['usecase']);
      } else {
        return launchInstance('us-elections-foo');
      }
    });
  }

  var launchInstance = function(usecase) {
    var id_token = localStorage.getItem('id_token');
    var rand = Math.floor((Math.random() * 100) + 1);

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
        retrieve_update_instances();
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

  var retrieve_update_instances = function() {
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
            "Authorization": id_token 
          },
          success: function (data){
            runningInstances = data;
            if (usecases) {
              update_instances(data, usecases);
            } else {
              window.setTimeout( 
                check_for_instances_and_usecases(200)
                ,200);
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
      window.setTimeout( 
              check_for_instances_and_usecases()
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
              var tabs = tabjq.tabs({heightStyle: "auto"});
              var ul = tabs.find( "ul" );
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
              editors[usecase + '-' + language] = CodeMirror.fromTextArea(textarea.get()[0], {mode: 'javascript', autoRefresh: true})

/*
              var editor = CodeMirror.fromTextArea(
                  textarea[0], {
                  mode: 'shell',
                  lineNumbers: true
              });
*/
              tabs.tabs("refresh"); 
              $( "#tabs" ).tabs( "refresh" );
              $( "#accordion" ).accordion( "refresh" );
              tabs.tabs({
                active: 0,
                activate: codeTabActivate(usecase, language)
                });
          }
        });
      })(language, usecase, username, password, ip, httpPort, boltPort, tabjq);
    }
  }

  var codeTabActivate = function(usecase, language) {
    return function(event, ui) {
      $( "#tabs" ).tabs( "refresh" );
      $( "#accordion" ).accordion( "refresh" );
      editors[usecase + '-' + language].refresh();
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

  var show_usecases = function(usecases) {
    var oList = $('#usecaseList')
    var uList = $('<ul>', {id: 'usecaseList', style: 'display: none'})
    for (var usecaseNum in usecases) {
      (function (ucname) {
        var usecase = usecases[usecaseNum]
        var li = $('<li/>')
          .attr('class', 'usecaseListItem')
          .appendTo(uList);
        var divUsecase = $('<div/>')
          .appendTo(li)
          .attr('id', 'usecase:' + ucname);
        var divUsecaseImage = $('<div/>')
          .attr('class', 'usecase-div-image')
          .appendTo(divUsecase);
        var imgUsecaseImage = $('<img/>')
          .attr('class', 'usecase-img')
          .attr('src', usecase.logo)
          .appendTo(divUsecaseImage);
        var divUsecaseDescription = $('<div/>')
          .attr('class', 'usecase-div-description')
          .appendTo(divUsecase);
        var paraUsecaseDescription = $('<p/>')
          .text(`${usecase.name} - ${usecase.description}`)
          .appendTo(divUsecaseDescription);
        var paraUsecaseLaunchButton = $('<p/>')
          .appendTo(divUsecaseDescription);
        var buttonUsecaseLaunch = $('<button/>')
          .attr('type', 'submit')
          .attr('class', 'btn-launch')
          .attr('data-usecase', usecase.name)
          .text('Get Sandbox')
          .appendTo(paraUsecaseLaunchButton);
        var divUsecaseConnections = $('<div/>')
          .attr('class', 'connectionsList')
          .appendTo(divUsecaseDescription);
        var divUsecaseClear = $('<div/>')
          .attr('class', 'clear')
          .appendTo(divUsecase);

        window.addEventListener("runningInstance", function (event) {
          var sandboxId = event.detail.sandboxId;
          if (event.detail && event.detail.usecase && event.detail.usecase == ucname) {
              $('*[data-usecase="' + ucname + '"]').hide();
              var currentConnections = 
                divUsecaseConnections.find(`*[data-sandboxid="${event.detail.sandboxId}"]`)
              var divConnectionInfo = $('<div/>')
                  .attr('class', 'connectionInfoItem')
                  .attr('data-connectioninfo', `${event.detail.ip}:${event.detail.port}`)
                  .attr('data-sandboxid', event.detail.sandboxId)
                  .append(
                    $('<div/>')
                      .attr('class', 'connectionInfoItemTabContainer')
                      .append($('<ul/>')
                        .append($('<li/>')
                          .append($('<a/>')
                            .attr('href','#tabs-connection-info')
                            .text('Connection Info')))
                        .append($('<li/>')
                          .append($('<a/>')
                            .attr('href','#tabs-datamodel')
                            .text('Data Model')))
                        .append($('<li/>')
                          .append($('<a/>')
                            .attr('href','#tabs-code')
                            .text('Code')))
                        .append($('<li/>')
                          .append($('<a/>')
                            .attr('href','#tabs-logs')
                            .text('Logs'))))
                      .append($('<div/>')
                        .attr('id','tabs-connection-info')
                        .attr('class','tabs-connection-info')
                        .append($('<p/>')
                          .text('Neo4j Browser: ')
                          .append($('<a/>')
                            .attr('href', `http://${event.detail.ip}:${event.detail.port}/`)
                            .attr('target', '_blank')
                            .text(`http://${event.detail.ip}:${event.detail.port}/`)
                          ))
                        .append($('<p/>')
                          .html(`username: ${event.detail.username}<br />` +
                                `password: ${event.detail.password}`)))
                      .append($('<div/>')
                        .attr('id','tabs-datamodel')
                        .append($('<img/>')
                          .attr('src', event.detail.modelImage)
                          .attr('width', '100%')))
                      .append($('<div/>')
                        .attr('id','tabs-code')
                        .attr('class','tabs-code')
                        .append($('<div/>')
			  .attr('class', `tabs-code-${event.detail.usecase}`)
			  .append($('<ul />')))
			.tabs({heightStyle: "auto"}))
                      .append($('<div/>')
                        .attr('id','tabs-logs')
                        .append($('<textarea/>')
                          .attr('id', `logs-${event.detail.sandboxId}`)
                          .attr('value',"")
                          .text(`loading... for task ${event.detail.taskId}\n`)
                          ))
                      .tabs({
                        heightStyle: "auto",
                        activate: function(event, ui) {
                          if (ui.newTab[0].outerText == "Logs") {
                            if (! ui.newPanel[0].lastChild.CodeMirror) {
                              var editor = CodeMirror.fromTextArea(
                                ui.newPanel[0].firstChild, {
                                mode: 'shell',
                                lineNumbers: true
                              })
    			      editor.setValue('Loading...');
                              retrieve_logs(editor, sandboxId, null);
                            }
                          }
                        }
                      }));
                    /*
                    $('<a/>')
                      .attr('href', `http://${event.detail.ip}:${event.detail.port}/`)
                      .text(`http://${event.detail.ip}:${event.detail.port}/`)
                    );*/
$('.connectionInfoItemTabContainer').tabs("refresh");
$('.tabs-code').tabs("refresh");
              if(currentConnections.length == 0) {
/*
$('.connectionInfoItem').resizable({
         handles: 's',
         alsoResize: '.ui-tabs-panel'
     });
$('.tabs-code').resizable({
         handles: 's',
         alsoResize: '.ui-tabs-panel'
     });
*/
                divConnectionInfo.appendTo(divUsecaseConnections);
                retrieve_show_code_snippets(event.detail.usecase, event.detail.username, event.detail.password, event.detail.ip, event.detail.port, event.detail.boltPort, divConnectionInfo.find(`.tabs-code-${event.detail.usecase}`));
              } else {
                // only replace if pending item.  TODO, preempt earlier to prevent dom build
                if (currentConnections.data('sandboxStatus') == 'pending'){
                  currentConnections.replaceWith(divConnectionInfo);
                }
              }
              $('.connectionInfoItemTabContainer').tabs("refresh");
	      $('.tabs-code').tabs("refresh");
          }    
        });
        window.addEventListener("startingInstance", function (event) {
          if (event.detail && event.detail.usecase && event.detail.usecase == ucname) {
              $('*[data-usecase="' + ucname + '"]').hide();
              var currentConnections = 
                divUsecaseConnections.find(`*[data-sandboxid="${event.detail.sandboxId}"]`)
              if(currentConnections.length == 0) {
                $('<div/>')
                    .attr('data-sandboxid', event.detail.sandboxId)
                    .attr('data-sandbox-status', 'pending')
                    .text("Starting instance for this usecase.  Give me a few seconds please")
                    .appendTo(divUsecaseConnections);
              }
	      $('.connectionInfoItemTabContainer').tabs("refresh");
	     $('.tabs-code').tabs("refresh");
          }    
        });
      })(usecases[usecaseNum].name);
    }
    oList.replaceWith(uList);
    // update buttons
    launchButtonAction();
  }

  var update_instances = function(instances, usecases) {
    console.log(instances);
    console.log(usecases);

    $('.jumbotron').hide();
    $('.marketing').hide();

    sandboxListDiv = $("#sandboxList");
    activeUsecases = {}

    for (var instanceNum in instances) {
      var instance = instances[instanceNum]
      instance.username = 'neo4j';

      activeUsecases[instance.usecase] = true;

      sandboxDiv = $("#sandbox_template").clone();
      sandboxDiv
      .removeAttr('id')
      .attr('data-sandboxid', instance.sandboxId);
      sandboxDiv.find('.navbar-brand').text(instance.usecase);

      sandboxDiv.find('.connection a').click(update_sandbox_panel('connection', instance.sandboxId));
      var connectionDiv = sandboxDiv.find('.panel-body').find('.connection');
      connectionDiv.empty().append(
            $('<p/>')
              .text('Neo4j Browser: ')
              .append($('<a/>')
                .attr('href', `http://${instance.ip}:${instance.port}/`)
                .attr('target', '_blank')
                .text(`http://${instance.ip}:${instance.port}/`)
              ))
            .append($('<p/>')
              .html(`username: ${instance.username}<br />` +
                    `password: ${instance.password}`));


      sandboxDiv.find('.datamodel a').click(update_sandbox_panel('datamodel', instance.sandboxId));
      var datamodelDiv = sandboxDiv.find('.panel-body').find('.datamodel');
      datamodelDiv.empty().append($('<img/>')
                          .attr('src', instance.modelImage)
                          .attr('width', '100%'));


      sandboxDiv.find('.code a').click(update_sandbox_panel('code', instance.sandboxId));
      var codeDiv = sandboxDiv.find('.panel-body').find('.code');
      codeDiv.empty().append($('<div/>')
                          .attr('class', `tabs-code-${instance.usecase}`)
                          .append($('<ul />')))
                        .tabs({heightStyle: "fill"}).tabs("refresh");
      retrieve_show_code_snippets(instance.usecase, instance.username, instance.password, instance.ip, instance.port, instance.boltPort, codeDiv.find(`.tabs-code-${instance.usecase}`));


      sandboxListDiv.append(sandboxDiv);
    }

    availableForLaunchCount = 0;
    for (var usecaseNum in usecases) {
      usecase = usecases[usecaseNum]
      ucname = usecase.name

      /* always show blank sandbox for testing TODO remove */
      if ((! ucname in activeUsecases) || (ucname == 'blank-sandbox')) {
        console.log("Allow " + ucname);
        columnNum = (availableForLaunchCount % 3 ) + 1;
        panelDiv = $('<div/>').attr('class', 'panel panel-primary')
          .append(
            $('<div/>').attr('class', 'panel-heading').text(ucname)
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
        launchButtonAction();
        availableForLaunchCount++;
      }
    }
    $("#sandboxListContainer").show();
    $("#usecaseListContainer").show();
  }

  var update_sandbox_panel = function(panelName, sandboxId) {
    return function (event) {
        if (! event.target.parentElement.classList.contains('active')) {
            // this element isn't active, set it active and update content
            $( event.target.parentElement.parentElement ).find('li').removeClass('active');
            $( event.target.parentElement ).addClass('active');
            $( event.target ).closest('.panel').find('.panel-body').children().hide();
            $( event.target ).closest('.panel').find('.panel-body').find('.' + panelName).show();
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
    $('.btn-logout').hide();
    $('.btn-login').show();
    $('.marketing').show();
    $('.jumbotron').show();
    $('#sandboxList').empty();
    $('#sandboxListContainer').hide();
    window.location.href = window.location.href;
  };

$(document).ready(function() {
  $('.btn-login').click(function (e) {
    loginButtonAction(e);
  });
  $('.btn-logout').click(function(e) {
    e.preventDefault();
    logout();
  })
  var profile = localStorage.getItem('profile');
  if (profile) {
    try {
      show_profile_info(JSON.parse(profile))    
    } catch (err) {

    }
  }
  retrieve_usecases();

  if (localStorage.getItem('id_token')) {
    // TODO FIGURE OUT WHY DOUBLE LOADING
    retrieve_update_instances();
    $('.btn-login').hide();
    $('.btn-logout').show();
  }
});

