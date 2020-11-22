$(document).ready(function(){
    const limit = $('.limit-cross')
    limit[0].style.display = "none"
    let first_click = true;

    let eventData = JSON.parse(localStorage.getItem('eventData'));
    if(eventData !== null){
        const new_url_obj1 = $('.new1');
        const new_url_obj2 = $('.new2');
        const new_url_obj3 = $('.new3');
        const new_long_url_obj1 = $('.new-long1')
        const new_long_url_obj2 = $('.new-long2')
        const new_long_url_obj3 = $('.new-long3')
        const url_div1 = document.getElementsByClassName("url1")
        const url_div2 = document.getElementsByClassName("url2")
        const url_div3 = document.getElementsByClassName("url3")
        const url_hr1 = document.getElementsByClassName("url-hr1")
        const url_hr2 = document.getElementsByClassName("url-hr2")
        const eventData_length = eventData.length

        if (eventData_length === 1) {
            new_url_obj1.text("http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
            new_url_obj1.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
            new_long_url_obj1.text(eventData[eventData_length - 1].long_url)
            url_div1[0].style.display = "flex"
            url_div2[0].style.display = "none"
            url_div3[0].style.display = "none"
            url_hr1[0].style.display = "block"
            url_hr2[0].style.display = "none"
        }
        else if (eventData_length === 2) {
            new_url_obj1.text("http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
            new_url_obj1.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
            new_long_url_obj1.text(eventData[eventData_length - 1].long_url)
            new_url_obj2.text("http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
            new_url_obj2.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
            new_long_url_obj2.text(eventData[eventData_length - 2].long_url)
            url_div1[0].style.display = "flex"
            url_div2[0].style.display = "flex"
            url_div3[0].style.display = "none"
            url_hr1[0].style.display = "block"
            url_hr2[0].style.display = "block"
        }
        else {
            new_url_obj1.text("http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
            new_url_obj1.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
            new_long_url_obj1.text(eventData[eventData_length - 1].long_url)
            new_url_obj2.text("http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
            new_url_obj2.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
            new_long_url_obj2.text(eventData[eventData_length - 2].long_url)
            new_url_obj3.text("http://127.0.0.1:5000/" + eventData[eventData_length - 3].short_url);
            new_url_obj3.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 3].short_url);
            new_long_url_obj3.text(eventData[eventData_length - 3].long_url)
            url_div1[0].style.display = "flex"
            url_div2[0].style.display = "flex"
            url_div3[0].style.display = "flex"
            url_hr1[0].style.display = "block"
            url_hr2[0].style.display = "block"
        }
    }
    else {
        const url_div1 = document.getElementsByClassName("url1")
        const url_div2 = document.getElementsByClassName("url2")
        const url_div3 = document.getElementsByClassName("url3")
        const url_hr1 = document.getElementsByClassName("url-hr1")
        const url_hr2 = document.getElementsByClassName("url-hr2")
        url_div1[0].style.display = "none"
        url_div2[0].style.display = "none"
        url_div3[0].style.display = "none"
        url_hr1[0].style.display = "none"
        url_hr2[0].style.display = "none"
    }

    $('#urlInput').change(function(){
        if ($('#urlInput').val() === ""){
            $('.updateButton').css('background-color', '#1b3987');
            $('.updateButton').text("Shorten");
            first_click = true;
        }
    })

    $('.updateButton').on('click', function() {
        const update_button = $('.updateButton')
        if (first_click === true){
            update_button.css('background-color', '#1b3987');
            update_button.text("Shorten");
            const url = $('#urlInput').val();
            let req = $.ajax({
                url: '/add_link',
                type: 'POST',
                data: { url: url }
            });

            req.done(function(data){
                if (data.new_link === undefined) {
                    const limit = $('.limit-cross')
                    limit[0].style.display = "block"
                    function sleep(ms) {
                        return new Promise(resolve => setTimeout(resolve, ms));
                    }
                    sleep(4000).then(() => {
                        limit[0].style.display = "none"
                    })
                    first_click = true
                }
                else {
                    const limit = $('.limit-cross')
                    limit[0].style.display = "none"
                    $('#urlInput').val("http://127.0.0.1:5000/" + data.new_link);
                    const new_url_obj1 = $('.new1');
                    const new_url_obj2 = $('.new2');
                    const new_url_obj3 = $('.new3');
                    const new_long_url_obj1 = $('.new-long1')
                    const new_long_url_obj2 = $('.new-long2')
                    const new_long_url_obj3 = $('.new-long3')
                    const url_div1 = document.getElementsByClassName("url1")
                    const url_div2 = document.getElementsByClassName("url2")
                    const url_div3 = document.getElementsByClassName("url3")
                    const url_hr1 = document.getElementsByClassName("url-hr1")
                    const url_hr2 = document.getElementsByClassName("url-hr2")
                    if (typeof(Storage) !== "undefined") {
                        let eventData = JSON.parse(localStorage.getItem('eventData'));
                        if(eventData == null){
                            eventData=[];
                            url_div1[0].style.display = "none"
                            url_div2[0].style.display = "none"
                            url_div3[0].style.display = "none"
                            url_hr1[0].style.display = "none"
                            url_hr2[0].style.display = "none"
                        }
                        const details = {};

                        details["long_url"] = data.long_link;
                        details["short_url"] = data.new_link;

                        eventData.push(details);

                        localStorage.setItem('eventData', JSON.stringify(eventData))
                        const eventData_length = eventData.length
                        if (eventData_length === 1) {
                            new_url_obj1.text("http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
                            new_url_obj1.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
                            new_long_url_obj1.text(eventData[eventData_length - 1].long_url)
                            url_div1[0].style.display = "flex"
                            url_div2[0].style.display = "none"
                            url_div3[0].style.display = "none"
                            url_hr1[0].style.display = "block"
                            url_hr2[0].style.display = "none"
                        }
                        else if (eventData_length === 2) {
                            new_url_obj1.text("http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
                            new_url_obj1.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
                            new_long_url_obj1.text(eventData[eventData_length - 1].long_url)
                            new_url_obj2.text("http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
                            new_url_obj2.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
                            new_long_url_obj2.text(eventData[eventData_length - 2].long_url)
                            url_div1[0].style.display = "flex"
                            url_div2[0].style.display = "flex"
                            url_div3[0].style.display = "none"
                            url_hr1[0].style.display = "block"
                            url_hr2[0].style.display = "block"
                        }
                        else {
                            new_url_obj1.text("http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
                            new_url_obj1.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 1].short_url);
                            new_long_url_obj1.text(eventData[eventData_length - 1].long_url)
                            new_url_obj2.text("http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
                            new_url_obj2.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 2].short_url);
                            new_long_url_obj2.text(eventData[eventData_length - 2].long_url)
                            new_url_obj3.text("http://127.0.0.1:5000/" + eventData[eventData_length - 3].short_url);
                            new_url_obj3.attr('href', "http://127.0.0.1:5000/" + eventData[eventData_length - 3].short_url);
                            new_long_url_obj3.text(eventData[eventData_length - 3].long_url)
                            url_div1[0].style.display = "flex"
                            url_div2[0].style.display = "flex"
                            url_div3[0].style.display = "flex"
                            url_hr1[0].style.display = "block"
                            url_hr2[0].style.display = "block"
                        }
                        $('.updateButton').text("Copy");
                    }
                    else {
                        console.log("Failed")
                    }
                }
            });
            first_click = false
        }
        else {
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }
            const copy_text = document.getElementById('urlInput');
            copy_text.select();
            document.execCommand("copy");
            update_button.text("Copied!");
            update_button.css('background-color', '#649949');
            sleep(1000).then(() => {
                update_button.css('background-color', '#1b3987');
                update_button.text("Copy");
            })
        }
    });
});