@0xd4165899f0751dc0;

struct MediumDocumentTiny {
  mediumId @0 :UInt32;
  rating @1 :Text;
  mediumHash @2 :Text;
  width @3 :UInt32;
  height @4 :UInt32;
  filesize @5 :UInt64;
  insertDate @6 :Text;
  innateTagNames @7 :List(Text);
  searchableTagNames @8 :List(Text);
  absentTagNames @9 :List(Text);
}