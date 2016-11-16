$(document).ready(function() {

  var listener = function(event) {
    $('.btn-login').hide();
    $('.btn-launch').show();
    event.source.close();
    localStorage.setItem('id_token', event.data.token)
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
    window.addEventListener('message', function(event) {
      clearInterval(pollInterval);
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

  $('.btn-launch').click(function (e) {
    var id_token = localStorage.getItem('id_token');
    $.ajax
    ({
      type: "POST",
      url: "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxRunInstance",
      dataType: 'json',
      data: JSON.stringify({ "usecase": "elections2016" }),
      contentType: "application/json",
      async: true,
      headers: {
        "Authorization": id_token 
      },
      success: function (data){
        retrieve_show_instances();
      }
    });
  });

  var show_profile_info = function(profile) {
     $('.nickname').text(profile.nickname);
     $('.btn-login').hide();
     $('.avatar').attr('src', profile.picture).show();
     $('.btn-logout').show();
  };

  var retrieve_show_instances = function() {
    var id_token = localStorage.getItem('id_token');
    if (id_token) {
        $('.btn-login').hide();
        $('.btn-logout').show();
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
        $('.btn-launch').show();
    }
  }

  var show_instances = function(instances) {
    var iList = $('#instanceList')
    for (var instanceNum in instances) {
        var li = $('<li/>')
          .appendTo(iList);
        var a = $('<a/>')
          .attr('href', 'http://' + instances[instanceNum].ip + ':' + instances[instanceNum].port)
          .text(instances[instanceNum].usecase)
          .appendTo(li);
    }
  }

  var launch_instance = function(usecase) {
  }

  var logout = function() {
    localStorage.removeItem('id_token');
    window.location.href = "/";
  };

  // Display user information
  retrieve_show_instances();
});
