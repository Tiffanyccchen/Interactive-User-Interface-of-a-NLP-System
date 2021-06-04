$(function(){

    /*重置按鈕按下去全部都清空回原始設定*/
    $("button[type = reset]").click(function(){
        $("div#context").text("");
        $("textarea").val("");
        $("input#checkslider").trigger("change").prop("checked", false); /*進階設定滑動回復*/
    })

    /*進階設定滑動時變化*/
    $("input#checkslider").on("change", function(){

        /*若沒有滑開 : 勾選框不能運作*/
        $("input[name='checkpar']").prop("disabled", !this.checked);

        /*若沒有滑開 : 圓形框 & 文字框不能運作 / 勾選框/圓形框取消勾選(會影響到文字顏色變化) / 文字框輸入清空*/
        if (!$(this).checked){
            $("input[type='radio']").prop("disabled",true);
            $("textarea[name = 'input']").prop("disabled",true);
            $("textarea#charnuminput").prop("disabled",true);

            $("input[name='checkpar']").prop("checked", false);
            $("input[type='radio']").prop("checked", false);

            $("textarea[name = 'input']").val("");
            $("textarea#charnuminput").val("");
        }
    }).trigger('change')

    /*勾選框被勾選時變化*/
    $("input[name = 'checkpar']").on("change", function(){
        var $box = $(this);

        /*若沒有勾選-> 同一條件 文字框/圓形框不能運作*/
        $box.siblings().prop("disabled",!this.checked);

        if ($box.is(":checked")){
            var group = "input:radio[class='" + $box.attr("class") + "']";
            if (group != "input:radio[class='repeatmentionls[]']" && group != "input:radio[class='compressionls[]']") {
                
                /*勾選-> 同一條件 預設程度變藍*/
                $( group + "[name = 'degree2']").prop("checked", true);

            } else if  (group == "input:radio[class='repeatmentionls[]']") {
                
                /*勾選-> 同一條件 預設程度變藍*/
                $( group + "[name ='degree4']").prop("checked", true);

            } else {
                
                /*勾選-> 同一條件 預設程度變藍*/
                $( group + "[name ='degree1']").prop("checked", true);
            }

            var text = "textarea[class='" + $box.attr("class") + "']";
            if (text == "textarea[class='charnumls[]']") {
                /*勾選-> 若勾到字數 預設字數出現*/
                $(text).val("150");
            }
        }

        /*若沒有勾選->同一條件 圓形框不選擇 / 文字框清空*/
        if (!$box.is(":checked")) {
            var group = "input:radio[class='" + $box.attr("class") + "']";

            // the checked state of the group/box on the other hand will change
            // and the current value is retrieved using .prop() method
            $(group).prop("checked", false);

            var text = "textarea[class='" + $box.attr("class") + " highlightref']";
            $(text).val("");
        } 

    }).trigger("change")

    /*某條件某程度圓形框被選擇時其他程度自動消失*/
    $("input:radio").on("click", function(){
        var $box = $(this);

        if ($box.is(":checked")) {
            var group = "input:radio[class='" + $box.attr("class") + "']";

            /*其他程度自動消失*/
            $(group).prop("checked", false);
            $box.prop("checked", true);

        } else {
            $box.prop("checked", false);
        }
    })   

    /*按下摘要按鈕後的變化*/
    $("button[type = submit]").click(function(event){
        $.ajax({
            type : 'POST',

            /*將介面之輸入傳遞到router為/abc的函式入口(在PIESim_kernel.py裡面*/
            url: '/abc',

            /*傳遞到之輸入及設定*/
            data:{
                text : $("div#context").text(),
                titletext: $("textarea#title").val(),
                querytext : $("textarea#necinput").val(),
                querynotext : $("textarea#notnecinput").val(),
                charnumval : $("textarea#charnuminput").val(),
                queryval : $("input[type = 'radio'][class='neckeywordls[]']:checked").val(),
                querynoval : $("input[type = 'radio'][class='notneckeywordls[]']:checked").val(),
                centval : $("input[type = 'radio'][class='repeatmentionls[]']:checked").val(),
                positionval : $("input[type = 'radio'][class='firstparals[]']:checked").val(),
                redundantval : $("input[type = 'radio'][class='redundantls[]']:checked").val(),
                compressionval : $("input[type = 'radio'][class='compressionls[]']:checked").val()
            }
        })  

        /*將router為/abc的函式入口產生的資料傳回介面*/
        .done(function(data){
            if (data.error){
                $("textarea#summary").val(data.error);
            }
            else{
                /*顯示摘要文字在摘要文字框*/
                $("textarea#summary").val(data.summary);

                /*顯示摘要產生通知*/
                alert('摘要產生!');
            }
        });
        event.preventDefault();      
    })

    /*將網站文章內容貼上到原文文字框 (div標籤原本是不能貼上的 (而為何用div不用textarea是為了highlighy))*/
    $("div#context").on("paste", function(event) {
        event.preventDefault();

        /* 只保留文字 & 不要保留原本顏色 or 字型*/
        var pastedData = event.originalEvent.clipboardData.getData('text');
        document.execCommand('insertText', false, pastedData);
    })
      
    /*define a highLightAt function to replace subtexts with highlighted ones */
    function highLightAt(idxpairs) {  
        var highlighttext = '';
        var last_idx = 0;

        /* 針對每一個highlight片段的成對起始index與結束index */
        for(i = 0 ; i < idxpairs.length ; i++){

            /* highlight 起始index & 結束 index */
            var start_idx = parseInt(idxpairs[i][0]);
            var end_idx = parseInt(idxpairs[i][1]);
            highlighttext += ($('div#context').text().substring(last_idx, start_idx) + '<span class="highlight">' + $('div#context').text().substring(start_idx, end_idx) + '</span>'); 
            last_idx = end_idx;
        }  

        /* 將剩下文字加上 */
        highlighttext += $('div#context').text().substr(last_idx);
        return highlighttext;  
    }  

    /*游標移至highlight參照文字框時之變化*/
    $("textarea.highlightref").focus(function(event){
        $.ajax({
            type : 'POST',

            /*將介面之輸入傳遞到router為/def的函式入口(在PIESim_kernel.py裡面*/
            url: '/def',
            data:{

                /*原文的內容*/
                text : $("div#context").text(),

                /*參照文字框之class name*/
                selector : $(this).attr('class'),

                /*參照文字框的內容*/
                highlightreftext: $(this).val()
            }
        })  
        .done(function(data){
            if (data.match_idxs){
                var match_idxs = JSON.parse(data.match_idxs);
                var highlighttext = highLightAt(match_idxs);

                /*原文樣式內容變成highlighttext*/
                $("div#context").html(highlighttext);
            }
        });
        event.preventDefault();      
    });  

    /*游標移出highlight參照文字框時之變化*/
    $("textarea.highlightref").blur(function(event){
        event.preventDefault();    
        
        /*將原文中highlight樣式移除 == 黃色移除*/  
        $("span").removeClass("highlight");
    });      
}) 


