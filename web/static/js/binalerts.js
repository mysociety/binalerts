// binalerts js for dustbin lorry animation

var mySocDelays = { 'init': 1000, 'busy': 1200, 'drive1px': 7, 'repeat': 5000, 'continue': 20 };
var $mySocLines; // usually, 1 line == 1 week 
var mySocLineIndex = 0;
var $mySocCollectionDays;
var $mySocLorry;

function mySocParkLorryAtDepot(nextStop, delayType){
  if (delayType == 'init') { // XXX should create the lorry div here
    $mySocLorry = $('#mysoc-bin-lorry');
  } else  { // switch to next line
    mySocLineIndex = (mySocLineIndex+1) % $mySocLines.size();
    $mySocLorry.detach().prependTo($mySocLines[mySocLineIndex]);
  }
  $mySocLorry.css('left', -$mySocLorry.width());
  $mySocLorry.show();
  setTimeout("mySocDriveLorry(" + nextStop + ")", mySocDelays[delayType])
}

function mySocDriveLorry(nextStop){
  var targetLeft = 0; // left position of lorry's next destination
  var nextAction = ""; // what to do when it gets there
  if (nextStop == $mySocCollectionDays.size()){ // end of all collections
    nextAction = "mySocParkLorryAtDepot(0, 'repeat')";
    targetLeft = $mySocLorry.parent().width();
  } else {
    var targetDiv = $($mySocCollectionDays[nextStop]);
    if (targetDiv.parent().attr('id') != $mySocLorry.parent().attr('id')) {
      nextAction = "mySocParkLorryAtDepot(" + nextStop + ",'continue')";
      targetLeft = $mySocLorry.parent().width();
    } else {
      nextAction = "mySocDriveLorry("+ (nextStop+1) +")";
      targetLeft = $(targetDiv).position().left - Math.round(($mySocLorry.width()-$(targetDiv).width())/2);
    }
  }
  var journeyDistance = targetLeft - $mySocLorry.position().left;
  $mySocLorry.animate(
    {'left' : targetLeft },
    journeyDistance * mySocDelays['drive1px'],
    function() {
      setTimeout(nextAction, mySocDelays['busy'])
    }  
  )
}

$(function() {
  $mySocCollectionDays = $('.mysoc-bin-collection');
  if ($mySocCollectionDays.size() > 0){
    $mySocLines = $('.mysoc-bin-week');
    mySocParkLorryAtDepot(0, 'init')
  }
 });
