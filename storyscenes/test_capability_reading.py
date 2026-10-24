"""Reading QA must lose answers when their actual narrative support disappears."""
import unittest

from capabilities.core import CapabilityError
from capabilities.reading import Document, Reader, Statement


def document():
    return Document(title="A refused request", statements=(
        Statement(id="request", text='Bea asked Ada, "Will you certify the seal?"',
                  kind="request", focus="r1", answer="Bea asked Ada to certify the seal.",
                  event_ids=("ask:1",), entity_ids=("ada", "bea", "seal"), reference_tick=0),
        Statement(id="reply", text='Ada answered Bea, "No, I cannot certify it."',
                  kind="response", focus="r1", answer="Ada declined Bea's request. She did not certify the seal.",
                  event_ids=("decline:1", "ask:1"), needs=("request",), reference_tick=0,
                  question="How did Ada answer Bea?"),
        Statement(id="reason", text='"I have not inspected its inside," Ada explained.',
                  kind="why", focus="r1", answer="Ada said she had not inspected the inside. That was her stated reason for declining.",
                  event_ids=("decline:1",), needs=("reply",), reference_tick=0,
                  question="Why did Ada decline?"),
    ))


class CapabilityReadingTests(unittest.TestCase):
    def test_answer_and_followup_use_same_event_and_reference_time(self):
        reader = Reader(document())
        response = reader.ask("response", "r1")
        self.assertTrue(response.supported)
        reason = reader.follow_up("why")
        self.assertTrue(reason.supported)
        self.assertEqual(reason.statement_ids, ("request", "reply", "reason"))
        self.assertEqual(reason.reference_tick, response.reference_tick)

    def test_mask_reason_reply_or_target_abstains(self):
        for hidden in ("reason", "reply", "request"):
            with self.subTest(hidden=hidden):
                reader = Reader(document().mask([hidden]))
                self.assertFalse(reader.ask("why", "r1").supported)
        reader = Reader(document().mask(["request"]))
        self.assertFalse(reader.ask("response", "r1").supported)

    def test_unknown_or_ambiguous_time_does_not_guess(self):
        first = Statement(id="old", text="At six the light was red.", kind="color", focus="light",
                          answer="The light was red at six.", event_ids=("old:1",), reference_tick=6)
        second = Statement(id="new", text="At seven the light was green.", kind="color", focus="light",
                           answer="The light was green at seven.", event_ids=("new:1",), reference_tick=7)
        reader = Reader(Document(title="Two times", statements=(first, second)))
        self.assertFalse(reader.ask("color", "light").supported)
        self.assertTrue(reader.ask("color", "light", reference_tick=6).supported)
        self.assertFalse(reader.ask("location", "hidden_object").supported)
        self.assertFalse(reader.follow_up("why").supported)

    def test_exact_spans_and_no_simulator_access(self):
        doc = document()
        for span, statement in zip(doc.spans(), doc.statements):
            self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
        self.assertEqual(len(Reader(doc).questions()), 2)
        self.assertFalse(hasattr(Reader(doc), "state"))

    def test_unbacked_assertion_rejected(self):
        with self.assertRaises(CapabilityError):
            Document(title="No", statements=(Statement(id="bad", text="A claim.", kind="fact",
                     focus="x", answer="Unbacked.", event_ids=()),))


if __name__ == "__main__":
    unittest.main()
