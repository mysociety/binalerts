// binalerts js for dustbin lorry animation

// mySocCollectionDays is declared in the body of the page
// Monday is 0 a la Python

function mySocParkLorryAtDepot(delayType){
  $('#mysoc-bin-lorry').css('left', -2 * mySocLorryWidth);
  $('#mysoc-bin-lorry').show();
  setTimeout("mySocDriveLorry(0)", mySocDelays[delayType])
}

function mySocDriveLorry(nextStop){
  var targetLeft = 0;
  var nextAction = "";
  if (nextStop == mySocCollectionDays.length){ // end of the week
    targetLeft = $('.mysoc-bin-week').width() + 2 * mySocLorryWidth;
    nextAction = "mySocParkLorryAtDepot('repeat')";
  } else {
    var targetDiv = $('.mysoc-bin-day')[mySocCollectionDays[nextStop]];
    targetLeft = $(targetDiv).position().left - Math.round((mySocLorryWidth-$(targetDiv).width())/2);
    nextAction = "mySocDriveLorry("+ (nextStop+1) +")";
  }
  var journeyDistance = targetLeft - $('#mysoc-bin-lorry').position().left;
  $('#mysoc-bin-lorry').animate(
    {'left' : targetLeft },
    journeyDistance * mySocDelays['drive1px'],
    function() {
      setTimeout(nextAction, mySocDelays['busy'])
    }  
  )
}

var mySocDelays = { 'init': 1000, 'busy': 1200, 'drive1px': 7, 'repeat': 5000 };
var mySocLorryWidth;

$(function() {
  if (mySocCollectionDays.length > 0){
    for (day in mySocCollectionDays){
      if (mySocCollectionDays[day] < 0 || mySocCollectionDays[day] > 6){
        return // bad day of week
      }
    }
    mySocLorryWidth = $('#mysoc-bin-lorry').width();
    mySocParkLorryAtDepot('init')
  }
 });
