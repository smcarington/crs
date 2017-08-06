$(document).ready(function() {
    // Websocket version of poll_admin interface. Used for updating votes only.
    // Start/stop information can still be sent by ajax.
    
    // Located in a hidden input because of template rendering
    var url_prepend = document.getElementById("url_prepend").value;
    url_prepend = url_prepend.substring(0, url_prepend.length-1);

    var course_pk = document.getElementById("course_pk").value
    var poll_pk  = document.getElementById("poll_pk").value
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var votesock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + "/ws/" + url_prepend+ "/query_live/" + course_pk + "/" + poll_pk + "/");

    // Update votes.
    votesock.onmessage = function(message) {
        var data = JSON.parse(message.data);

        if (data.hasOwnProperty('state')) { //Message is a vote update
            // Data should include the current state of the question and the primary
            // key of the question. Extract this.
            preData = data['state'].split('-');
            pk      = preData[0];
            state   = preData[1];
            delete data['state']
            if (state == 'True') { // Voting is live
                $("#votes-"+pk).html("Total Votes: "+data['numVotes']);
                delete data['numVotes'];
                Object.keys(data).forEach(function (key) {
                    $("#"+key).html("("+data[key]+" votes)");
                });
            } else if (state == 'False') { // Voting has ended, so clear total votes
                $("#votes-"+pk).html('');
            }
        } else { // Update from start/stop button
            if (data['action']=='endall') {
                $('[id^="response"]').html(data['response']);
                setTimeout( function() {$('[id^="response"]').html('')}, 2000);
            } else {
                $response = $("#response_"+pk);
                $response.html(data['response']);
                setTimeout( function() {$response.html('')}, 2000);
            }

            // Check to see if the question has been restarted.
            // When resetting a question, we must replace the choice pk's. In this instance only, the
            // response item contains a pk map whose keys are the old pk's, and whose values are the new pk's
            if (data.hasOwnProperty('pkMap')) {
                pkMap = data['pkMap'];
                $("#"+pk+"-choices>ol>li>p>small").each( function() {
                    // Determine the old pk, which is the field for the new pk
                    idString = $(this).attr('id').split('-');
                    newIDString = pkMap[idString[0]]+"-votes";
                    $(this).attr('id', newIDString);
                    $(this).html("(0 votes)");
                });
            }

            // To make the 'voters' anchor work, we need to update to the current poll whenever we hit start
            // Look for the anchor whose data-id matches the question primary key
            if (action == 'start') {
                $anchor = $("a.voters[data-id="+pk+"]");
                url_string = $anchor.attr("href");

                // Need to do some regex magix
                re = /(\d+)\/(\d+)\//;
                match=re.exec(url_string);
                new_poll = (parseInt(match[2]) + 1).toString();
                new_url = url_string.replace(match[0], match[1]+"/"+new_poll+"/");

                $anchor.attr("href", new_url);
            }

            // Make the backgrounds work:
            // Turn off the active one
            $('.question_live').removeClass('question_live');
            if (action == 'start') {
                $('div.row.div-'+pk).addClass('question_live');
            }
        }
    };

    // Poll administration 
    $('[id^="check"]').click( function() {
        var question = $(this).attr('id').split('_')[1];
        var live     = $(this).is(':checked');
        $.post('/'+url_prepend+'/make_live/', {question: question, live: live}, 
            function(data) {
                $response = $("#response_"+question);
                $response.html(data['response']);
                setTimeout( function() {$response.html('')}, 2000);
        }, "json");
    });
    
    // When a button is clicked (that is, the start/stop/reset buttons), determine 
    // the appropriate action and send the server the appropriate response
    $('button').click( function() {
        preData = $(this).attr('id').split('_');
        action  = preData[0];
        pk      = preData[1];

        var message = {
            action: action,
            questionpk: pk
        }
        votesock.send(JSON.stringify(message))
    });

    // Opens choices option in poll administration
    $("[id^='open']").click( function () {
        qpk = $(this).attr('id').split('-')[1];
        $target = $("#"+qpk+"-choices");
        if ($target.is(":visible") ) {
            $target.hide(300);
        } else {
            $target.show(300);
        }
    });

    // Helper function for swapping two elements
    function swapDiv(element, order) {
        if (order == "up") { 
            element.parent().insertBefore(element, element.previousSibling);
        } else if (order == "down") {
            element.parentNode.insertBefore(element.nextSibling, element);
        }
    }

    // Listener for moving arrows.
    $("[id^='arrow']").click( function() {
        preData = $(this).attr('id').split('-');
        pre    = preData[0];
        action = preData[1];
        pk     = preData[2];
        // Find the appropriate div. It is the grandparent, not great grandparent
        $thisDiv = $(this).parents("#global-"+pk)
        if (action == "up") {
            $thisDiv.insertBefore($thisDiv.prev("[id^='global']"));
        } else if (action == "down") {
            $thisDiv.next("[id^='global']").insertBefore($thisDiv);
        }
        $.post('/change_question_order/', 
               {action:action, pk:pk},
               "json")
            .always( function(data) 
                {   var json = JSON.parse(data);
                    console.log(json['response']); 
                }
            );
    });

    // Check to see how many votes have been cast
    // Replaced by websockets
//    function voteCheck() {
//        // Get the course primary key from the url
//        var course_pk = location.href.split('/')[4]
//
//        $.get(
//            '/query_live/', 
//            {course_pk: course_pk},
//            function(data) {
//                preData = data['state'].split('-');
//                pk      = preData[0];
//                state   = preData[1];
//                delete data['state']
//                if (state == 'True') {
//                    $("#votes-"+pk).html("Total Votes: "+data['numVotes']);
//                    delete data['numVotes'];
//                    Object.keys(data).forEach(function (key) {
//                        $("#"+key).html("("+data[key]+" votes)");
//                    });
//                } else if (state == 'False') {
//                    $("#votes-"+pk).html('');
//                }
//            }, 
//        "json");
//        setTimeout(voteCheck, 2000);
//    }
//    // Start the method to check if votes have been cast
//    setTimeout(voteCheck, 2000);

    $("#slides_live").click( function() {
        $('[type="checkbox"]').click();
    });

    $("a.voters").click(function() {
        window.open(this.href, "popupWindow", "width=600, height=600, scrollbars=yes");
        return false;
    });

});
