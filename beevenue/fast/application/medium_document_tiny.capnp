@0xd4165899f0751dc0;

struct MediumDocumentTiny {
  mediumId @0 :UInt32;
  rating @1 :Text;
  innateTagNames @2 :List(Text);
  searchableTagNames @3 :List(Text);
  absentTagNames @4 :List(Text);
}