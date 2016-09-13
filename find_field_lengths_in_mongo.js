

function findMax() {
    var max = 0;


    db.storedfilenode.find().forEach(function(doc) {
        var currentLength = doc.materialized_path.length;
        if (currentLength > max) {
           max = currentLength;
        }
    });

    print(max);
}

use osf20130903
findMax();
