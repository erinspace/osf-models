

function findMax() {
    var max = 0;


    db.fileversion.find().forEach(function(doc) {
        if (doc.content_type === null) return;
        var currentLength = doc.content_type.length;
        if (currentLength > max) {
           max = currentLength;
        }
    });

    print(max);
}

use osf20130903
findMax();
