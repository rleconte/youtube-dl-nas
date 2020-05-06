var wsEventBus = null;  //eventBus register flag
var thdYn = false;

$(function () {

    if(!thdYn){
        $(".table-responsive").hide();
    }else{
        $(".table-responsive").show();
    }

    //websocket support
    if (!window.WebSocket) {
        if (window.MozWebSocket) {
            window.WebSocket = window.MozWebSocket;
        } else {
            $('#messages').append("<li>Your browser doesn't support WebSockets.</li>");
        }
    }

    if(wsEventBus==null){
        wsEventBus = new WebSocket(window.location.protocol.replace('http','ws')+'//'+window.location.host+'/websocket');
        console.log("Server EventBus websocket was created"+ window.location.host);

        wsEventBus.onopen = function(evt) {
            messagesTxt("[MSG], WebSocket connection opened.");
        }

        wsEventBus.onmessage = function(evt) {
            thdYn = true;
            messagesTxt( evt.data);
        }

        wsEventBus.onclose = function(evt) {
            messagesTxt("[MSG], WebSocket connection closed.");
        }

    }

    $(document).on("click","#send",function(){

        var data={};
        data.url = $("#url").val();
        data.resolution = $("#selResolution").val();

        $.ajax({
            method : "POST"
            , url : "/youtube-dl/q"
            , data : JSON.stringify(data)
            , dataType : "json"
            , contentType: "application/json"
            , success:function(data,status){
                window.setTimeout(function(){
                    messagesTxt(data.msg);
                },400);
                //
            }
            , error:function (jqXHR, textStatus, errorThrown) {
                if(jqXHR.status==422){
                    custAlert("The service name cannot be used. Please select again.", "red");

                }else if(jqXHR.status==500){
                    custAlert(errorThrown +":Internal error. Please try again later.","red");
                }else{
                    alert("Internal error. Please try again later.");
                }
                console.log("jqXHR"+jqXHR);
                console.log("jqXHR"+jqXHR.status);
                console.log("textStatus"+textStatus);
                console.log("errorThrown"+errorThrown);
            }
        });

        $('#message').val('').focus();

        return false;
    });


    function messagesTxt(msg){

        var noti = msg.split(",");
        console.log("noti :"+noti[0])
        if(noti[0] == "[COMPLETE]"){
            if(thdYn){
                $(".table-responsive").show();
            }
            $("#completeInfo").append("<tr><td>"+noti[1]+"</td><td>"+noti[2]+"</td></tr>");
        }else if(noti[0] == "[QUEUE]"){
            $('#queue').html('<li>' + noti[1] + '</li>');
        } else{
            $('#messages').html('<li>' + noti[1] + '</li>');
        }
    };

});
