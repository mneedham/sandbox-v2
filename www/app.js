$(document).ready(function() {

  var listener = function(event) {
    JSON.stringify(event.data);
  }
 
  if (window.addEventListener){
    addEventListener("message", listener, false)
  } else {
    attachEvent("onmessage", listener)
  }

  $('.btn-login').click(function(e) {
    window.open("https://auth.neo4j.com/index.html",
                "login");
  });

  $('.btn-logout').click(function(e) {
    e.preventDefault();
    logout();
  })

  var show_profile_info = function(profile) {
     $('.nickname').text(profile.nickname);
     $('.btn-login').hide();
     $('.avatar').attr('src', profile.picture).show();
     $('.btn-logout').show();
  };

  var retrieve_show_instances = function() {
    var id_token = localStorage.getItem('id_token');
    $.getJSON("https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetRunningInstancesForUser?auth0_key=mykey", function(data) {
      show_instances(data);
    }); 
  }

  var show_instances = function(instances) {
    alert(JSON.stringify(instances));
  }

  var logout = function() {
    localStorage.removeItem('id_token');
    window.location.href = "/";
  };

  // Display user information
  retrieve_show_instances();
});
