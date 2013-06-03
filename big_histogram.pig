register s3n://uw-cse-344-oregon.aws.amazon.com/myudfs.jar

-- load 0.5TB 
raw = LOAD 's3n://uw-cse-344-oregon.aws.amazon.com/btc-2010-chunk-*' USING TextLoader as (line:chararray);

-- parse each line into ntriples
ntriples = foreach raw generate FLATTEN(myudfs.RDFSplit3(line)) as (subject:chararray,predicate:chararray,object:chararray);

--group the n-triples by subject column
subjects = group ntriples by (subject) PARALLEL 50;

-- flatten the objects out (because group by produces a tuple of each object
-- in the first column, and we want each object ot be a string, not a tuple),
-- and count the number of tuples associated with each object
count_by_subject = foreach subjects generate flatten($0), COUNT($1) as count PARALLEL 50;

-- group subjects by count (x)
group_by_count = group count_by_subject by (count) PARALLEL 50;

-- count the number of tuples that have count x (y)
count_y = foreach group_by_count generate flatten($0),COUNT($1) as count PARALLEL 50;

-- store results
store count_y into 's3n://jardel-coursera/histogram-results';
