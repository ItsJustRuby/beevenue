@0x8a9b1977d80e5328;

using MDT = import "medium_document_tiny.capnp";

struct AllMediumDocumentTiny {
  all @0 :List(MDT.MediumDocumentTiny);
}