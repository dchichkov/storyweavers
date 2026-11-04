"""Scene-sized prose. Each branch reflects a local action or persistent fact."""


def render(scene_id, p, before, after):
    if scene_id == "borrow":
        return (
            "Jo had promised Mina the toy cart for her seedling run, and its front wheel "
            "answered every push with a dry rattle. At Len's courtyard repair bench, Jo "
            "asked for the spanner. “Borrow it,” Len said, “but don't make a nut tighter "
            "just because it makes noise.” Mina held the cart steady. Jo heard the warning, "
            "and the rattle, but trusted the obvious answer."
        )
    if scene_id == "chalk_names":
        return (
            "Mina took a stub of chalk from the bench. “It isn't Len's cart,” she said, "
            "writing both their names on the wooden side. Jo wanted to wipe the uneven "
            "letters clean, but Mina grinned. “Now he can't lend it to anyone else.” The "
            "mark stayed beside the wheel."
        )
    if scene_id == "first_attempt":
        if after["jo.swapped_tool"]:
            tool = "The borrowed spanner slipped; Len exchanged it for his adjustable one. "
        else:
            tool = "Len's spanner fitted the wheel nut. "
        if p.bench_level:
            brace = "Jo set the cart on the level bench. "
        else:
            brace = "The sloping bench let the cart creep, so Jo wedged its frame. "
        return (
            brace + tool + "“Loose,” Jo said. One careful turn pinched the hub against the "
            "fork. The wheel stopped turning, but the rattle still clicked from side to side. "
            "Mina raised an eyebrow. Jo's fingers stayed on the handle."
        )
    if scene_id == "reinspect":
        return (
            "The wheel shifted sideways in Mina's hands, although its nut was already "
            "pinched tight. Jo crouched and saw daylight where a thin spacer should sit "
            "between hub and fork. “So it wasn't loose,” Mina said. “I made it worse,” Jo "
            "answered. The missing washer explained both the rattle and the wheel that "
            "would no longer turn."
        )
    if scene_id == "measure_story":
        return (
            "Len didn't tell them what to do. He showed a pale groove on his old spanner. "
            "“I once tightened a wheel until it couldn't turn. The noise was somewhere "
            "else.” Mina looked from the groove to Jo. “Listening first would have saved "
            "you a turn.” Jo nodded. The little lesson belonged to this cart now, not just "
            "Len's toolbox."
        )
    if scene_id == "admit_error":
        return (
            "Jo set the spanner down. “I guessed before I checked. I pinched the wheel, "
            "and the rattle wasn't the nut.” Mina's shoulders eased. “Thanks for saying it "
            "before I had to.” She pointed to the empty spacer gap. “Now let's find the "
            "right thing, not a thing that merely fits.” Jo felt smaller, then steadier."
        )
    if scene_id == "keep_face":
        return (
            "Jo brushed the grit from both palms. “Something's wrong with the cart. Give "
            "me a minute.” Mina saw the pinched wheel but didn't argue. “A minute, then "
            "we decide together.” Jo wanted to sound certain; instead the silence made "
            "the first guess feel heavier. The missing spacer lay plainly between them."
        )
    if scene_id == "repair":
        load_line = (
            "With three pots aboard, Jo set one on the bench shelf before touching the axle. "
            if p.cart_load == 3 else "They cleared the light load from the wheel before working. "
        )
        return (
            load_line + "A spare washer waited in Len's parts tin. Jo placed it between hub "
            "and fork, then eased the nut until the wheel had room to turn without wobbling. "
            "Mina spun it once. The rattle was gone. “That's the sound I wanted,” she said, "
            "not the silence of a stuck wheel."
        )
    if scene_id == "park_it":
        return (
            "Len's parts tin held no washer. Jo could have cut a cardboard shim, but it "
            "wouldn't hold the wheel safely. “No more guessing,” Jo said. They loosened "
            "the pinch, chocked the cart at the bench, and took every pot to the exchange "
            "by hand. The cart stayed out of service; its bed became a sign stand: "
            "SPACER NEEDED — DO NOT ROLL."
        )
    if scene_id == "test_roll":
        if p.cart_load == 3:
            load = "Mina carried the extra pot from the shelf while Jo rolled the two-pot load. "
        elif p.cart_load == 1:
            load = "Mina set one pot in the bed and walked beside Jo. "
        else:
            load = "Mina set the two pots in the bed and walked beside Jo. "
        if p.admission_style == "early":
            partner = "This time Mina kept a hand on the handle too. "
        else:
            partner = "Mina watched closely while Jo pushed alone. "
        return (
            load + partner + "They crossed the courtyard to the exchange table. The wheel "
            "turned cleanly over the paving; no sideways knock came back. Mina unloaded "
            "the seedlings. “Now I can set them out before the neighbors arrive.” Jo "
            "finally let go of the handle."
        )
    if scene_id == "mark_out":
        return (
            "Jo rocked the axle by hand, never pushing the cart. The side play was still "
            "there, and the rattle answered at once. Mina carried the pots to the exchange "
            "table while Len braced the cart at the bench. They wrote a plain warning on "
            "its bed and left the wheel alone. No one had to pretend the repair was done."
        )
    if scene_id == "ending_repaired":
        callback = " Their chalk names still marked the shared cart." if after["cart.name_marked"] else ""
        if after["jo.heard_tip"]:
            callback += " Jo remembered Len's advice to listen first."
        return (
            "Jo parked the empty cart by the bench. “You were right to stop me,” Jo said. "
            "Mina touched the quiet wheel. “We checked it together this time.” Len took "
            "back the spanner and used it to snug his loose vise screw. The cart had carried "
            "the seedlings; the borrowed tool had earned its keep." + callback
        )
    if scene_id == "ending_rebuilt":
        callback = " Their chalk names still marked the shared cart." if after["cart.name_marked"] else ""
        if after["jo.heard_tip"]:
            callback += " Jo remembered Len's advice to listen first."
        return (
            "Jo parked the empty cart by the bench. “I should've told you I made it worse,” "
            "Jo said. Mina nodded, still watching the wheel. “You did tell me. Next time, "
            "sooner.” Len used the returned spanner to snug his loose vise screw. Mina "
            "wheeled the seedlings into place, and Jo walked beside her." + callback
        )
    if scene_id == "ending_stopped":
        callback = " Their chalk names still marked the cart's sign stand." if after["cart.name_marked"] else ""
        if after["jo.heard_tip"]:
            callback += " Jo remembered Len's advice to listen first."
        admission = (
            "Jo had admitted the bad guess early, so Mina asked Jo to write the sign. "
            if p.admission_style == "early" else
            "Jo owned the first mistake before they left, and Mina let the apology stand. "
        )
        return (
            "The cart stayed chocked beside the bench, its warning facing the courtyard. "
            "Mina had carried the seedlings to the exchange herself; they were already on "
            "the table. " + admission + "Len used the returned spanner to secure his vise. "
            "The cart was not repaired, but nobody hid the fault or risked its wheel." + callback
        )
    raise ValueError(f"No prose for scene: {scene_id}")
