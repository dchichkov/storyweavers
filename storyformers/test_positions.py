"""Local positional features and their integration with cached annotations."""

from copy import deepcopy
import json
import unittest

from .annotation import EXAMPLES, annotation_request, story_tokens
from .annotate import extract_response
from .positions import add_positions
from .test_annotation import response


class PositionTests(unittest.TestCase):
    def test_global_and_sentence_indices_include_spaces_and_punctuation(self):
        rows = add_positions(story_tokens("Lily ran. Ben sat."))
        self.assertEqual([row["position"]["token"] for row in rows], list(range(9)))
        self.assertEqual(rows[0]["position"], {"token": 0, "sentence": 0, "in_sentence": 0})
        self.assertEqual(rows[4]["token"], " ")
        self.assertEqual(rows[4]["position"], {"token": 4, "sentence": 0, "in_sentence": 4})
        self.assertEqual(rows[5]["token"], "Ben")
        self.assertEqual(rows[5]["position"], {"token": 5, "sentence": 1, "in_sentence": 0})

    def test_closing_quotes_and_repeated_end_marks_do_not_add_sentences(self):
        rows = add_positions(story_tokens('"Stop?!"  Then go.'))
        by_token = {row["token"]: row for row in rows}
        self.assertEqual(by_token["Then"]["position"]["sentence"], 1)
        self.assertEqual(by_token["Then"]["position"]["in_sentence"], 0)
        self.assertEqual(by_token['"']["position"]["sentence"], 0)
        quoted = add_positions(story_tokens('Lily ran. "Ben sat."'))
        opening = next(row for row in quoted if row["token"] == '"')
        self.assertEqual(opening["position"], {"token": 5, "sentence": 1, "in_sentence": 0})
        ben = next(row for row in quoted if row["token"] == "Ben")
        self.assertEqual(ben["position"]["in_sentence"], 1)

    def test_decimal_and_common_titles(self):
        rows = add_positions(story_tokens("Dr. Ava paid 3.14 coins. Ben waved!"))
        by_token = {row["token"]: row for row in rows}
        self.assertEqual(by_token["Ava"]["position"]["sentence"], 0)
        self.assertEqual(by_token["3.14"]["position"]["sentence"], 0)
        self.assertEqual(by_token["Ben"]["position"]["sentence"], 1)

    def test_empty_whitespace_only_and_idempotent_nonmutating_overlay(self):
        self.assertEqual(add_positions([]), [])
        original = [{"token": " ", "attributes": [{"name": "test", "value": "kept"}]}]
        snapshot = deepcopy(original)
        rows = add_positions(original)
        self.assertEqual(original, snapshot)
        self.assertEqual(add_positions(rows), rows)
        rows[0]["attributes"][0]["value"] = "changed"
        self.assertEqual(original, snapshot)

    def test_later_text_cannot_change_earlier_positions(self):
        prefix = story_tokens("Lily ran.")
        full = story_tokens("Lily ran. Ben sat. Ava waved.")
        self.assertEqual(add_positions(prefix), add_positions(full)[:len(prefix)])

    def test_positions_are_added_after_api_and_leave_request_unchanged(self):
        example = json.loads(EXAMPLES.read_text())[0]
        body = annotation_request(example["story"])
        before = deepcopy(body)
        rows, metadata = extract_response(example["story"], body, response(example["response"]))
        self.assertEqual(body, before)
        self.assertNotIn("position", body["text"]["format"]["schema"]["properties"]["annotations"]["items"]["properties"])
        self.assertTrue(all("position" in row for row in rows))
        self.assertEqual(metadata["position_encoding"]["index_base"], 0)
        self.assertEqual("".join(row["token"] for row in rows), example["story"])


if __name__ == "__main__":
    unittest.main()
