import argparse
import src.nhlstats.app
import src.nhlstats.logic.collector
import src.nhlstats.logic.analyst


def main():
    parser = argparse.ArgumentParser(description="NHL Stats App")
    parser.add_argument('-c', '--collect', action='store_true', help='Collect latest info')
    parser.add_argument('-w', '--web', action='store_true', help='Launch the website')
    parser.add_argument('-e', '--elo', action='store_true', help='Generate player ELO ratings based on current stats')
    args = parser.parse_args()

    if args.collect:
        src.nhlstats.logic.collector.collector()
    if args.web:
        src.nhlstats.app.app.run(debug=True, port=5001)
    if args.elo:
        src.nhlstats.logic.analyst.playerelo()


if __name__ == "__main__":
    main()