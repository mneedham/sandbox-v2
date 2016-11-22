$(document).ready(function() {

  var runningSandboxes = [];

  var listener = function(event) {
    $('.btn-login').hide();
    $('.btn-launch').show();
    //$('#logs').show();
    event.source.close();
    localStorage.setItem('id_token', event.data.token)
    localStorage.setItem('profile', event.data.profile)
    show_profile_info(event.data.profile)
    retrieve_show_instances();
  }
 
  if (window.addEventListener){
    addEventListener("message", listener, false)
  } else {
    attachEvent("onmessage", listener)
  }

  var pollInterval;

  $('.btn-login').click(function (e) {
    win = window.open("https://auth.neo4j.com/index.html",
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
                      "https://auth.neo4j.com/index.html")
      }, 6000);
  });

  $('.btn-logout').click(function(e) {
    e.preventDefault();
    logout();
  })

  var launchButtonAction = function() {
    $('.btn-launch').click(function (e) {
      $('.btn-launch').hide();  
      var id_token = localStorage.getItem('id_token');
      if (! id_token) {
        return $('.btn-login').trigger(e);  
      }
      if (e.target.dataset && e.target.dataset['usecase']) {
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
      url: "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxRunInstance",
      dataType: 'json',
      data: JSON.stringify({ "usecase": usecase}),
      contentType: "application/json",
      async: true,
      headers: {
        "Authorization": id_token 
      },
      success: function (data){
        retrieve_show_instances();
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

  var retrieve_show_instances = function() {
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
          url: "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetRunningInstancesForUser",
          dataType: 'json',
          async: true,
          headers: {
            "Authorization": id_token 
          },
          success: function (data){
            show_instances(data);
          }
        });
        //retrieve_logs(editor, null);
        $('.btn-launch').show();
    }
  }

  var retrieve_show_usecases = function() {
    $.ajax
    ({
      type: "GET",
      url: "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetUsecases",
      dataType: 'json',
      async: true,
      headers: {
      },
      success: function (data){
        show_usecases(data);
      }
    });
  }

  var retrieve_logs = function(editor, nextToken) {
    var id_token = localStorage.getItem('id_token');
    if (id_token) {
      data = {"usecase": "us-elections-2016"}
      if (nextToken) {
        data['nextToken'] = nextToken
      }
      $.ajax
      ({
        type: "GET",
        url: "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxRetrieveUserLogs",
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
    if (data.nextForwardToken) {
      setTimeout(retrieve_logs, 3000, editor, data.nextForwardToken);
    }
  } 

  var show_usecases = function(usecases) {
    var oList = $('#usecaseList')
    var uList = $('<ul>', {id: 'usecaseList'})
    for (var usecaseNum in usecases) {
      var li = $('<li/>')
        .html("<img class=\"usecase-image\" src=\"" + usecases[usecaseNum].logo + "\"><b>" + usecases[usecaseNum].name + "</b><br />" + usecases[usecaseNum].description + '<br /><button type="submit" class="btn-launch" data-usecase="' + usecases[usecaseNum].name + '">Launch Sandbox</button>' )
        .appendTo(uList);
      window.addEventListener("runningInstance", function (event) {
        if (event.detail && event.detail.usecase && event.detail.usecase == usecases[usecaseNum].name) {
            li.append("instance<br />");
        }    
      });
    }
    oList.replaceWith(uList);
    // update buttons
    launchButtonAction();
  }

  var show_instances = function(instances) {
    var oList = $('#instanceList')
    var iList = $('<ul>', {id: 'instanceList'})
    for (var instanceNum in instances) {
        var e = jQuery.Event('runningInstance');
        e.usecase = instances[instanceNum].usecase;
        window.dispatchEvent(new CustomEvent('runningInstance', {detail: { usecase: instances[instanceNum].usecase}}));
/*
        addEventListener("message", listener, false)
        if(instances[instanceNum].ip) {
            
            var li = $('<li/>')
              .appendTo(iList);
            var a = $('<a/>')
              .attr('href', 'http://' + instances[instanceNum].ip + ':' + instances[instanceNum].port)
              .text(instances[instanceNum].usecase + " - username: neo4j, password: " + instances[instanceNum].password )
              .appendTo(li);
        } else {
            setTimeout(retrieve_show_instances, 10000);
            var li = $('<li/>').text("Launching: " + instances[instanceNum].usecase)
              .appendTo(iList);
        }
*/
    }
    //oList.replaceWith(iList);
  }

  var logout = function() {
    localStorage.removeItem('id_token');
    window.location.href = "/sandbox-web/www/";
  };

  retrieve_show_usecases();
  retrieve_show_instances();
});
