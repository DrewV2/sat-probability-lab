import itertools
import math
import unittest

from satlab.model import (Counts, Settings, poisson_binomial, convolve, summarize,
                          scored_distribution, predict_test, predict_section)
from satlab.examples import example_modules
from satlab.database import connect, seed_demo, predict_attempt, search_topics
from satlab.similarity import embed, cosine_similarity


class ProbabilityTests(unittest.TestCase):
    def test_dp_matches_exhaustive_enumeration(self):
        ps = [1, .5, 1/3, .25, 0, .8]
        expected = dict.fromkeys(range(len(ps)+1), 0.)
        for outcomes in itertools.product((0, 1), repeat=len(ps)):
            mass = math.prod(p if x else 1-p for x,p in zip(outcomes, ps))
            expected[sum(outcomes)] += mass
        actual = poisson_binomial(ps)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k])

    def test_moments(self):
        ps = [.99, .5, .5, 1/3, .25]
        result = summarize(poisson_binomial(ps))
        self.assertAlmostEqual(result['mean'], sum(ps))
        self.assertAlmostEqual(result['variance'], sum(p*(1-p) for p in ps))

    def test_pretest_matches_enumerating_positions(self):
        n, k = 6, 4
        raw = {i: float(i == k) for i in range(n+1)}
        expected = dict.fromkeys(range(n-1), 0.)
        for i,j in itertools.combinations(range(n), 2):
            expected[k-int(i<k)-int(j<k)] += 1/math.comb(n, 2)
        actual = scored_distribution(raw)
        for k,v in expected.items():
            self.assertAlmostEqual(actual.get(k, 0), v)

    def test_boundaries(self):
        for p, target in ((0, 0), (1, 25)):
            actual = scored_distribution(poisson_binomial([p]*27))
            self.assertAlmostEqual(actual[target], 1)

    def test_validation(self):
        for counts in (Counts(confident=28), Counts(confident=26.5, guess2=.5), Counts(confident=-1, wrong=28)):
            with self.assertRaises(ValueError):
                counts.validate('rw')
        with self.assertRaises(ValueError):
            Counts(confident=26, fill_right=1).validate('rw')
        for kwargs in ({'confidence':1.1}, {'coverage':1}, {'routing_width':0}, {'easy_cap':605}):
            with self.assertRaises(ValueError):
                Settings(**kwargs)
        with self.assertRaises(ValueError):
            poisson_binomial([float('nan')])

    def test_routing_and_point_support(self):
        settings = Settings()
        pair = example_modules()['rw']
        for route in ('easy', 'hard', 'unknown'):
            result = predict_section(*pair, 'rw', route=route, settings=settings, include_illustrative_scores=True)
            pmf = result['score_pmf']
            self.assertAlmostEqual(sum(pmf.values()), 1)
            self.assertTrue(all(200 <= k <= 800 and k%10 == 0 for k,p in pmf.items() if p > 0))
            if route == 'easy':
                self.assertTrue(all(k <= settings.easy_cap for k,p in pmf.items() if p > 0))
            if route != 'unknown':
                self.assertAlmostEqual(result['harder_route_probability'], float(route=='hard'))
        def harder(k):
            return predict_section(Counts(confident=k, wrong=27-k), pair[1], 'rw',
                                   include_illustrative_scores=True)['harder_route_probability']
        self.assertLess(harder(5), harder(25))

    def test_total_convolution_and_opt_in(self):
        modules = example_modules()
        self.assertIsNone(predict_test(**modules)['total_score_summary'])
        result = predict_test(**modules, include_illustrative_scores=True)
        total = result['total_score_pmf']
        self.assertAlmostEqual(sum(total.values()), 1)
        summary = result['total_score_summary']
        self.assertLessEqual(summary['low'], summary['median'])
        self.assertLessEqual(summary['median'], summary['high'])
        self.assertGreaterEqual(summary['interval_mass'], .9-1e-9)
        self.assertAlmostEqual(summary['mean'], sum(s['score_summary']['mean'] for s in result['sections'].values()))


class DataTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        seed_demo(self.db)

    def tearDown(self):
        self.db.close()

    def test_seed_is_repeatable_and_no_fake_labels(self):
        seed_demo(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0], 6)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM module_inputs').fetchone()[0], 24)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM attempts WHERE actual_rw IS NOT NULL OR actual_math IS NOT NULL').fetchone()[0], 0)

    def test_prediction_roundtrip(self):
        result = predict_attempt(self.db, 'demo-1')
        expected = predict_test(**example_modules(), include_illustrative_scores=True)
        self.assertEqual(result['total_score_summary'], expected['total_score_summary'])
        predict_attempt(self.db, 'demo-1', Settings(confidence=.95))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM predictions').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT score_status FROM predictions').fetchone()[0], 'illustrative_only')
        with self.assertRaises(ValueError):
            predict_attempt(self.db, "missing' OR 1=1 --")

    def test_sql_and_python_cosine_agree(self):
        query = embed('probability guessing distribution')
        result = search_topics(self.db, query)
        self.assertEqual(result.iloc[0]['topic_id'], 'guessing')
        vector = self.db.execute("SELECT embedding FROM topic_embeddings WHERE topic_id='guessing'").fetchone()[0]
        self.assertAlmostEqual(result.iloc[0]['similarity'], cosine_similarity(query, vector))
        for vector in ([0]*6, [1,2], [float('nan')]*6):
            with self.assertRaises(ValueError):
                search_topics(self.db, vector)


if __name__ == '__main__':
    unittest.main()
