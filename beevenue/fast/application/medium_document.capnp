@0x95c749da323bbe06;

struct MediumDocument {
  mediumId @0 :UInt32;
  mediumHash @1 :Text;
  mimeType @2 :Text;
  rating @3 :Text;
  width @4 :UInt32;
  height @5 :UInt32;
  filesize @6 :UInt64;
  insertDate @7 :Text;
  innateTagNames @8 :List(Text);
  searchableTagNames @9 :List(Text);
  absentTagNames @10 :List(Text);
  tinyThumbnail @11 :Data;
}