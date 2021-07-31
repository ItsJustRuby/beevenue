@0x95c749da323bbe06;

struct MediumDocument {
  mediumId @0 :UInt32;
  aspectRatio @1 :Text;
  mediumHash @2 :Text;
  mimeType @3 :Text;
  rating @4 :Text;
  tinyThumbnail @5 :Data;
  innateTagNames @6 :List(Text);
  searchableTagNames @7 :List(Text);
  absentTagNames @8 :List(Text);
}