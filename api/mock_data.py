from api.models import Record, Side, Stylus, Track

RECORDS: dict[str, Record] = {
    "1": Record(
        id="1",
        release_id="30348842",
        master_id="3453923",
        title="Papercuts",
        artist="Linkin Park",
        cover_image="ui/images/30348842.jpeg",
        linked=False,
        sides=[
            Side(id="A", tracks=[
                Track(title="Crawling", duration="03:29"),
                Track(title="Faint", duration="02:42"),
                Track(title="Numb/Encore", duration="03:25"),
                Track(title="Papercut", duration="03:05"),
                Track(title="Breaking The Habit", duration="03:16"),
            ]),
            Side(id="B", tracks=[
                Track(title="In The End", duration="03:36"),
                Track(title="Bleed It Out", duration="02:44"),
                Track(title="Somewhere I Belong", duration="03:34"),
                Track(title="Waiting For The End", duration="03:51"),
                Track(title="Castle Of Glass", duration="03:25"),
            ]),
            Side(id="C", tracks=[
                Track(title="One More Light", duration="04:15"),
                Track(title="Burn It Down", duration="03:50"),
                Track(title="What I've Done", duration="03:25"),
                Track(title="Qwerty", duration="03:22"),
                Track(title="One Step Closer", duration="02:37"),
            ]),
            Side(id="D", tracks=[
                Track(title="New Divide", duration="04:29"),
                Track(title="Leave Out All The Rest", duration="03:29"),
                Track(title="Lost", duration="03:19"),
                Track(title="Numb", duration="03:07"),
                Track(title="Friendly Fire", duration="02:56"),
            ]),
        ],
    )
}

STYLI: dict[str, Stylus] = {
    "1": Stylus(id="1", name="Sumiko Olympia", hours=89.6)
}
