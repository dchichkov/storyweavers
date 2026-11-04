"""Short, event-grounded scene prose for the puppet-theatre adventure."""


def render(scene_id, params, before, after):
    if scene_id == "borrow_kit":
        return (
            "At the empty stage, Leni held up the torn moon's control loop. “The rehearsal starts soon.” "
            "Jo glanced at the bare rod. “Then we borrow, not panic.” Mrs. Bell lent them her sewing kit "
            "after Jo promised to bring it straight back. Ivo watched from behind the curtain."
        )

    if scene_id == "find_moon":
        if params.curtain_weight == "heavy":
            return (
                "The heavy curtain swallowed a silver edge. Jo gathered the cloth and held it while Leni "
                "freed the moon from its fold. Ivo took the felt crescent gently. It was whole; the little "
                "loop meant to hold it to the rod was torn almost through."
            )
        return (
            "A silver edge glinted beneath the light curtain. Leni eased the cloth aside and lifted the "
            "moon free. Jo checked the painted sea below it. Ivo took the felt crescent carefully: it was "
            "whole, but the little loop that held it to the rod had torn almost through."
        )

    if scene_id == "button_vignette":
        if after["button.location"] == "friends":
            return (
                "Jo turned the sewing kit over and found a brass button caught in its cloth lining. "
                "“A spare anchor,” he said, offering it to Leni. She tested it against the torn loop. "
                "“This might do.” Ivo leaned closer to look, then stepped back to leave them room."
            )
        return (
            "Jo checked the sewing kit's lining for a spare button, but found only a loose thread. "
            "“No hidden treasure,” he said. Leni set the kit beside the moon and studied its old, "
            "cracked button. They would have to use what was already sound—or choose another way "
            "to finish the rehearsal."
        )

    if scene_id == "whisper_vignette":
        return (
            "Behind the curtain, Ivo whispered, “I don't like everyone watching my hands.” Jo paused "
            "instead of reaching for the rod. “Thanks for telling me. What would help?” Ivo came a step "
            "forward. “Let me hold it. Don't grab it if it wobbles.” Leni nodded and left the rod with him."
        )

    if scene_id == "repair_moon":
        repair = after["prop.repair"]
        if repair == "secure":
            if after["prop.fastener"] == "spare_button":
                return (
                    "Leni stitched the brass button through the sound part of the felt loop, passing the "
                    "long thread through twice. Jo kept the kit open and handed her the scissors. She tied "
                    "the knot underneath, not in a hurry. Ivo watched the moon take shape on its rod."
                )
            if after["prop.fastener"] == "cloth_loop":
                return (
                    "With enough rehearsal time, Leni bypassed the cracked button and sewed a new loop "
                    "through the firm felt. The sharp needle and long thread made a proper anchor. Jo "
                    "held the fabric flat; Ivo kept the rod steady. The moon hung straight again, though "
                    "they still needed to test it."
                )
            return (
                "The old button was sound, so Leni used the sharp needle and long thread to sew the "
                "torn loop firmly around it. Jo held the felt flat while she secured the knot underneath. "
                "Ivo kept the rod steady. The moon was attached again, but nobody called it safe until "
                "they had tried it."
            )
        if repair == "temporary":
            return (
                "The available thread and button let Leni make a temporary tie, but the blunt needle or "
                "short thread left no strong seam. “It may hold once,” she said. Jo kept a hand under the "
                "moon, and Ivo looked at the rod as if deciding how gently a test should go."
            )
        return (
            "The button was cracked, there was no spare, and the short thread offered no safe anchor. "
            "Leni used the kit's scissors to cut a dark cloth scrap for a shadow screen instead. “Not the "
            "repair we wanted,” she said. Jo placed the scrap beside the moon; Ivo stayed to help."
        )

    if scene_id == "test_moon":
        if after["prop.holds"]:
            return (
                "Jo lifted the rod and moved it gently from side to side. The moon swung, then stayed "
                "attached. He tried a slightly higher arc; the button and stitches held. Ivo reached for "
                "the rod. “May I?” This time Leni handed it over without taking the cue from him."
            )
        if after["prop.thread_snapped"]:
            return (
                "At Jo's gentle test, the temporary knot slipped and the thread snapped. Leni caught "
                "the moon before it reached the floor. “All right,” she said, disappointed but calm. "
                "Ivo turned the loose crescent in his hands. It could still make a good shadow."
            )
        return (
            "There was no firm attachment to test. Jo lifted the moon by hand while Leni steadied the "
            "rod; they agreed not to pretend it was ready to swing. Ivo took the felt crescent carefully. "
            "“We can still use its shape,” he said, looking toward the curtain."
        )

    if scene_id == "set_stage":
        if after["stage.mode"] == "puppet":
            return (
                "Ivo chose the rod, and Leni opened the curtain for his cue. Jo moved the painted boat "
                "to its mark. “Tell me when the moon should cross,” Leni said. Ivo pointed just after "
                "the boat turned. The three positions made sense together; no one had to take the puppet "
                "out of his hands."
            )
        if before["prop.holds"]:
            return (
                "The repair held, but Ivo was not ready to work the rod in front of the room. He chose "
                "the moon as a hand-held silhouette instead. Leni left the curtain half drawn and Jo "
                "cleared a small space for the shadow. The rehearsal could belong to Ivo without making "
                "him stand exposed."
            )
        return (
            "The moon was loose, so Jo left the curtain half drawn and Leni set the stage for shadows. "
            "Ivo held the crescent where its outline could cross the cloth. The rod cue was gone, but "
            "the boat still needed a moon to find its way. They had a new version ready to perform."
        )

    if scene_id == "ending_rod":
        return (
            "Ivo guided the repaired moon across the painted sea while Leni spoke for the boat and Jo "
            "gave its captain a booming voice. The crescent stayed on through the final cue. After the "
            "rehearsal, Jo returned Mrs. Bell's useful sewing kit to the workroom. Ivo was smiling when "
            "the curtain closed."
        )

    if scene_id == "ending_shadow":
        if before["prop.holds"]:
            reason = "The repair held, but Ivo chose a shadow rather than the exposed rod."
        elif before["prop.repair"] == "temporary":
            reason = "The temporary stitch had snapped, so Ivo carried the loose moon into the light."
        else:
            reason = "The loop could not be secured, so Ivo carried the loose moon into the light."
        return (
            f"{reason} Leni voiced the boat and Jo made its captain sound enormous; Ivo swept the "
            "crescent across the curtain until the boat found home. They finished the scene together, "
            "not the way they had planned but all the way to its ending. Jo returned the sewing kit "
            "afterward, with its scissors and thread back in place."
        )

    raise ValueError(f"No prose for scene: {scene_id}")
