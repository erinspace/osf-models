

function findMax() {
    var max = 0;

    db.privatelink.find().forEach(function(doc) {
        var currentLength = doc.name.length;
        if (currentLength > max) {
           max = currentLength;
        }
    });

    print(max);
}

use osf20130903
findMax();
