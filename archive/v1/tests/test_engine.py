import unittest
from engine import retrieve, validate
class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'id':'a','excerpt':'I cannot see my SIP','summary':'Missing dashboard'}]
    def test_unknown_source_rejected(self):
        self.assertFalse(validate({'claims':[{'text':'Problem','evidence':[{'id':'fake','quote':'I cannot see'}]}]},self.rows))
    def test_fabricated_quote_rejected(self):
        self.assertFalse(validate({'claims':[{'text':'Problem','evidence':[{'id':'a','quote':'I stopped investing'}]}]},self.rows))
    def test_grounded_quote_accepted(self):
        self.assertTrue(validate({'claims':[{'text':'Visibility issue','evidence':[{'id':'a','quote':'I cannot see'}]}]},self.rows))
    def test_empty_and_malformed_rejected(self):
        for data in [None,{}, {'claims':[]}, {'claims':[None]}]: self.assertFalse(validate(data,self.rows))
    def test_unrelated_query_no_evidence(self):
        self.assertEqual(retrieve('pineapple',self.rows),[])
if __name__=='__main__': unittest.main()
