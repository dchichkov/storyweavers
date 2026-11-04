"""Short, state-grounded scene prose for The Storm Costume."""


def render(scene_id, params, before, after):
    if scene_id == "opening":
        return (
            "Ada had been trusted to keep the costume cupboard in order. Jo found her name crossed out "
            "beside STORM and a gold tunic marked MOON. She tried it at one shoulder; the seam pinched. "
            "‘I was promised Storm,’ Jo said. Ada looked from the label to her friend. ‘Then let's make "
            "them listen.’"
        )
    if scene_id == "borrow_cape":
        return (
            "The school cape hung on a high hook. Ada borrowed it, writing her name on the return card. "
            "She unfurled one corner. It made a soft rush that lifted the paper stars. ‘That could be our "
            "wind,’ she said. Jo smiled. Ada still held the cape; borrowing it had given their play a cue, "
            "not a new owner."
        )
    if scene_id == "mirror_vignette":
        if before["mirror.clean"]:
            return (
                "Jo stood before the clear mirror with the gold tunic held against her shoulder. The crossed-out "
                "Storm label showed behind her. ‘I look like the Moon, and not a comfortable one,’ she said. "
                "Ada watched Jo's face instead of offering a quick fix. ‘You still want Storm?’ ‘More than "
                "this,’ Jo answered."
            )
        return (
            "Fingerprints clouded the cupboard mirror, so Ada wiped a clean patch with her sleeve. Jo held "
            "the gold tunic against her shoulder; the crossed-out Storm label appeared behind her reflection. "
            "‘I look like the Moon, and not a comfortable one,’ she said. ‘You still want Storm?’ Ada asked. "
            "‘More than this,’ Jo replied."
        )
    if scene_id == "ribbon_vignette":
        return (
            "In the notions drawer, Jo found a thin silver ribbon. She tied it to the cape's clasp rather than "
            "the tight tunic. ‘A little moonlight for the storm,’ she said. Ada let Jo choose the detail. "
            "The ribbon stayed on the borrowed cape, ready to catch the stage light; it would go back to its "
            "drawer after the performance."
        )
    if scene_id == "consult_teacher":
        if after["teacher.answer"] == "matching_coat":
            return (
                "Ada found Mrs Bell at the doorway and showed her the crossed-out label. ‘Jo was promised "
                "Storm. Is there another costume?’ Mrs Bell checked the rail and brought over a roomy storm "
                "coat. ‘I'm sorry I missed this.’ Jo inspected the sleeves before taking it. ‘This one fits.’ "
                "They had time to try it before places."
            )
        return (
            "Ada found Mrs Bell carrying scenery boards and showed her the crossed-out label. Mrs Bell "
            "looked toward the assembly hall. ‘The right coat is over there, but it won't reach us before "
            "places.’ Jo spoke up: ‘I was promised Storm. Please don't change my part without asking.’ "
            "Mrs Bell apologized and hurried away; no missing costume appeared in the cupboard."
        )
    if scene_id == "refit_costume":
        if after["jo.costume_fits"] and after["jo.costume"] == "storm_coat":
            return (
                "Mrs Bell's storm coat was roomy at the shoulders and long enough for Jo to move. Jo raised "
                "both arms, then turned once. ‘I can breathe and still look like weather.’ Ada hung the "
                "pinching Moon tunic back on its rail. The promised role had its proper costume at last, "
                "because Jo had asked and the teacher had listened."
            )
        if after["jo.costume_fits"]:
            return (
                "The pin tin held just enough to let out the tunic's seam. Jo checked the loosened shoulder, "
                "then wore the altered gold cloth as a Storm costume instead of a Moon one. ‘It fits now, "
                "and the label can stop arguing,’ she said. Ada put the used pins safely aside. Jo had "
                "helped decide what the repair was for."
            )
        return (
            "The tunic's seam had no room, and the pin tin was empty. Ada began to suggest a quick fix, but "
            "Jo stepped back. ‘No pinning me into a part. I want Storm, not a costume that hurts.’ She put "
            "the Moon tunic on its rail. Ada listened. The costume still did not fit, but Jo's part was not "
            "being taken away."
        )
    if scene_id == "rehearse":
        if after["jo.plan"] == "storm_costume":
            detail = " The silver ribbon flashed at the clasp." if before["ribbon.chosen"] else ""
            return (
                "Backstage, Jo tested the sleeves while Ada swept the cape through the air. The fitted coat "
                "gave Jo room to turn; the cape made a gust on her cue. ‘Wait for my line,’ Jo said. Ada "
                "nodded and tried again, this time letting Jo lead the weather." + detail
            )
        if after["jo.plan"] == "storm_shadow":
            detail = " The silver ribbon winked at the edge." if before["ribbon.chosen"] else ""
            return (
                "The work lamp threw a bright square onto the scenery cloth. Ada raised the cape as a screen, "
                "and Jo practiced the Storm lines behind its moving shadow. ‘Not too fast,’ Jo said. Ada "
                "slowed the sweep until the dark shape rolled like a cloud." + detail
            )
        detail = " The silver ribbon flickered in the work light." if before["ribbon.chosen"] else ""
        return (
            "With no useful shadow from the work lamp, Ada and Jo made the cape a moving storm sail. Jo "
            "stamped out the thunder rhythm while Ada caught the cloth's edge. ‘On my word,’ Jo said. Ada "
            "waited, then sent a gust across the scenery. The cape had a job, and Jo had the cue." + detail
        )
    if scene_id == "performance":
        if after["jo.performance_style"] == "storm_costume":
            return (
                "The play paused for the Storm cue. Jo stepped forward in the coat that fit and spoke her "
                "lines without tugging at a seam. Ada swept the borrowed cape on the beat Jo had rehearsed. "
                "The wind crossed the painted sky; the audience clapped as the scene turned. Jo had played "
                "the role she was promised."
            )
        if after["jo.performance_style"] == "storm_shadow":
            return (
                "At the Storm cue, Jo stood behind the cape's shadow and spoke clearly into the hall. Ada "
                "moved the cloth across the lit scenery, and the dark shape rolled over the painted town. "
                "Jo's voice carried the thunder; the cape gave it weather. The audience followed the scene, "
                "not the costume label."
            )
        return (
            "At the Storm cue, Jo stamped a thunder rhythm and called the wind. Ada sent the borrowed cape "
            "sailing across the bright scenery cloth. It was not a fitted costume or a trick shadow, but the "
            "audience heard the weather in Jo's voice and saw it in the moving fabric. The hall answered "
            "with applause."
        )
    if scene_id == "ending_fit":
        return (
            "After the bow, Mrs Bell thanked Jo for speaking up and promised to correct the cast list. Jo "
            "kept the fitting Storm coat for the next scene. Ada returned the cape to its hook; its wind cue "
            "had helped the play, and school still owned it. ‘We fixed the costume and kept the part,’ Jo "
            "said. Ada agreed. The curtain was down, and their work was finished."
        )
    if scene_id == "ending_improvised":
        return (
            "After the bow, Mrs Bell apologized without making an excuse. Jo had played Storm without wearing "
            "the pinching Moon tunic. Ada returned the cape to its hook; its shadow or gust had carried the "
            "weather, and school still owned it. ‘That was my part,’ Jo said. ‘It was,’ Ada answered. The "
            "play was over, and Jo had not been made smaller to fit the wrong costume."
        )
    raise ValueError(f"No prose for scene: {scene_id}")
