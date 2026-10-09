// Sample reviews for quick testing. Products are limited to the model's
// training categories (Books, Electronics). Each click fills the box with a
// review where {subject} is replaced by a random subject from the product.
export const PRODUCTS = [
  {
    name: "Wireless Headphones",
    subjects: ["Aurelle X2 headphones", "Brisk Pulse 3", "Kestrel ANC headphones", "Lumen Air Pro", "Orbit Studio 5"],
    reviews: [
      { label: "Quick praise", text: "Great sound and comfy. Five stars." },
      { label: "Balanced", text: "Sound from the {subject} is clear and the bass is punchy, but the case is flimsy and the app is clunky. Good value overall if you can live with the quirks." },
      { label: "Long-term use", text: "I have used these {subject} for eight months on daily commutes. The battery still lasts a full workweek, though the left earcup started crackling after month five." },
      { label: "Detailed analysis", text: "I compared the {subject} against my previous pair across three areas. Noise cancelling blocks roughly two thirds of train noise, the codec handles compressed streams cleanly, and the touch controls misfire less often than the reviews suggest. The fit is the real trade-off: they clamp tightly, which helps with isolation but causes pressure after two hours." },
      { label: "Personal recommendation", text: "I bought the {subject} for my daughter's school runs and she loves them. I would recommend them to any parent who wants durable headphones that survive being dropped on pavement." },
      { label: "Complaint", text: "The {subject} stopped working after three weeks. Support was slow to reply." },
      { label: "Comparison", text: "Compared with my old pair, the {subject} sound noticeably better in the mids, but they weigh about 40 grams more. For a long flight I still prefer the lighter option." },
    ],
  },
  {
    name: "Laptop",
    subjects: ["Vantor 14", "Halden Air 13", "Quill Pro 16", "Nexar Book 15", "Ardent 14"],
    reviews: [
      { label: "Quick praise", text: "Fast, light, and the screen is gorgeous. Love it." },
      { label: "Balanced", text: "The keyboard on the {subject} is excellent and the trackpad is huge, but the fans are loud under load and the port selection is thin. For office work it is hard to beat." },
      { label: "Long-term use", text: "After a year of heavy use, the {subject} still has battery health above ninety percent. The hinge has loosened slightly, but performance has stayed consistent." },
      { label: "Detailed analysis", text: "I benchmarked the {subject} against two competing ultrabooks over a week of coding. Compile times were roughly twenty percent faster, sustained all-core performance dropped after about eight minutes, and thermals stayed under ninety degrees in most workloads. The display is bright and accurate, though the speakers lack bass." },
      { label: "Personal recommendation", text: "I switched from a desktop to the {subject} for my freelance design work and I would recommend it to anyone who needs something portable without giving up colour accuracy." },
      { label: "Complaint", text: "The {subject} had dead pixels out of the box. Returned it." },
      { label: "Comparison", text: "Next to my old machine, the {subject} is twice as fast on exports and half the weight. Battery life is shorter than advertised, though, closer to six hours than eight." },
    ],
  },
  {
    name: "Smartphone",
    subjects: ["Nimbus S9", "Pella Max", "Corvo 12", "Lyra Edge", "Tessa 7"],
    reviews: [
      { label: "Quick praise", text: "Camera is amazing, best phone I have owned." },
      { label: "Balanced", text: "The camera on the {subject} is sharp in daylight and the battery lasts two days. Low-light photos look over-processed, and the phone gets warm while gaming." },
      { label: "Long-term use", text: "Using the {subject} daily for seven months, the battery now lasts about a day and a half. Software updates have been regular and the phone still feels responsive." },
      { label: "Detailed analysis", text: "Over two weeks I tested the {subject} camera in forty scenes. Dynamic range is strong, autofocus is quick under twenty lux, and telephoto shots lose detail past 3x. The screen refresh rate adapts well, though it is not as smooth as the manufacturer claims in every app." },
      { label: "Personal recommendation", text: "My father is not technical, and the {subject} was the easiest switch he has made. I would recommend it to anyone who wants a dependable phone that just works." },
      { label: "Complaint", text: "The {subject} battery drains fast. Not worth the price." },
      { label: "Comparison", text: "Compared with last year's model, the {subject} has a far better zoom and a brighter screen. The charging speed is unchanged, which is a missed chance." },
    ],
  },
  {
    name: "Novel",
    subjects: ["Lantern Coast", "The Quiet Harbour", "Ashfall Letters", "Glass Orchard", "Winter Ledger"],
    reviews: [
      { label: "Quick praise", text: "Gripping from page one. Couldn't put it down." },
      { label: "Balanced", text: "The prose in {subject} is lovely and the setting is vivid, but the middle section drags and two subplots never resolve. Still a worthwhile read for fans of slow-burn mysteries." },
      { label: "Long-term use", text: "I have reread {subject} every autumn for six years. Each time I notice something new in the second act, and it still holds up better than most of the author's later work." },
      { label: "Detailed analysis", text: "{subject} works on three levels: a conventional detective plot, a study of grief in a small coastal town, and a formal experiment with unreliable chapter narrators. The third layer is where it succeeds most, though the pacing in chapters nine through twelve weakens the structure." },
      { label: "Personal recommendation", text: "I gave {subject} to my book club and we spent two hours arguing about the ending. I would recommend it to anyone who enjoys books that stay with them after the last page." },
      { label: "Complaint", text: "Didn't finish {subject}. Too slow for me." },
      { label: "Comparison", text: "Unlike the author's earlier trilogy, {subject} trades spectacle for interiority. Fans of the first book may find it quieter, but the ending is stronger than anything in the series." },
    ],
  },
  {
    name: "Cookbook",
    subjects: ["Ember Kitchen", "Plain Table", "Simmer & Rise", "Salt Route", "Slow Hearth"],
    reviews: [
      { label: "Quick praise", text: "Simple recipes, great results. Five stars." },
      { label: "Balanced", text: "Most recipes in {subject} work well and the photos are inspiring, but some ingredient lists are vague about quantities. Good for weeknight cooking, less so for baking." },
      { label: "Long-term use", text: "I have cooked from {subject} for three years. The lentil soup is still my go-to on cold nights, and the bread recipe has become a weekly habit for my household." },
      { label: "Detailed analysis", text: "{subject} is organised by technique rather than ingredient, which I found more useful than expected. Chapter three explains emulsions in four clear steps, and the tested timings are accurate to within about two minutes. The sauces section is weaker, with several recipes missing resting times." },
      { label: "Personal recommendation", text: "I bought {subject} as a gift for my brother who is just learning to cook. I would recommend it to any beginner who wants confidence in the kitchen." },
      { label: "Complaint", text: "Too many ingredients in {subject} I can't find locally." },
      { label: "Comparison", text: "Compared with the classic test kitchen books, {subject} is less rigorous on measurements but far more relaxed. It suits confident cooks better than anyone starting out." },
    ],
  },
];
