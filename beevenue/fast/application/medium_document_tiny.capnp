@0xd4165899f0751dc0;

struct MediumDocumentTiny {
  mediumId @0 :UInt32;
  rating @1 :Text;
  mediumHash @2 :Text;
  innateTagNames @3 :List(Text);
  searchableTagNames @4 :List(Text);
  absentTagNames @5 :List(Text);
}