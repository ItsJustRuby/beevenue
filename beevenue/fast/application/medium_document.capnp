@0x95c749da323bbe06;

struct MediumDocument {
  mediumId @0 :UInt32;
  mediumHash @1 :Text;
  mimeType @2 :Text;
  rating @3 :Text;
  innateTagNames @4 :List(Text);
  searchableTagNames @5 :List(Text);
  absentTagNames @6 :List(Text);
  tinyThumbnail @7 :Data;
}