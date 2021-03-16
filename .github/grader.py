#!/usr/bin/python

# To run as a script:
# python grader.py <data_dir> <submission file> <day number>
# python grader.py data/challenge3 day3subm.csv 3

import sys
import numpy as np
import pandas as pd
# from pathlib import Path


class Grader(object):
    def __init__(self,data_path,submission_path):
        self.columns = ['id', 'health', 'decline', 'bed', 'ventilator', 'oxygen', 'remdesivir',
                        'dexamethasone', 'plasma', 'casirivimab', 'chloroquine', 'total']

        self.reusable = [('ventilator', 10, 30), ('oxygen', 10, 20)]
        self.onetime  = [('remdesivir', 7, 30), ('dexamethasone', 20, 25),
                         ('plasma', 10, 15), ('casirivimab', 10, 15), ('chloroquine', 17, 10)]
        self.treatments = self.reusable+self.onetime

        # days = ['Day1data.xlsx', 'day2data.xlsx', 'day3data.xlsx']
        # days = ['day1data.csv']
        self.data = pd.read_csv(data_path,
                                header=1,
                                usecols=[0,1,2],
                                names=['id', 'health', 'decline'])
        self.submission = self._df_from_fname(submission_path)


    #public

    def validate_one(self, fname:str, day_num:int):
        try:
            return self._validate(fname, day_num)
        except AssertionError as e:
            print(f"Invalid entry: {e}")


    #def validate_multiple(self, day1, day2=None, day3=None):b


    #private

    def _validate(self, fname, day_num):
        df = self.submission
        data = self.data

        self._verify_column_names(df)
        self._verify_data_match(df, data)
        for treatment in self.treatments:
            self._verify_treatment(df, *treatment)
        self._verify_treatments_with_bed(df)
        self._verify_combo_constraints(df)
        return self._scorer(df, day_num)

    def _df_from_fname(self, fname):
        '''read either csv or xlsx'''
        ext = fname.split('.')[-1]
        if ext == 'csv':
            df = pd.read_csv(fname)
        elif ext == 'xlsx':
            df = pd.read_excel(fname)
        else:
            raise AssertionError("Filename must be in either csv or xlsx format")
        return df

    def _verify_column_names(self, df):
        '''verify the csv is well-formatted and treatments are spelled correctly'''
        for c in df.columns:
            assert c in self.columns, f"Column: {c} is not an accepted column name"

    def _verify_data_match(self, df, data):
        '''verify the ids, health, decline matches the day's data file'''
        dd = pd.merge(data, df, on=['id','health','decline'], how='left', indicator='exist')
        assert np.all(dd.exist=='both'), "submission does not match data on id, health, or decline"

    def _verify_treatment(self, df, name, qty, eff):
        '''verify that treatment counts and efficacies are correct'''
        if name in df.columns:
            m = df[name]==eff
            num_used = (m).sum()
            assert num_used <= qty, f"exceeded treatment quantity for {name}"
            assert np.all(df[name][~m]==0) , f"incorrect treatment efficacy used for {name}"

    def _verify_treatments_with_bed(self, df):
        '''verify that treatments only occur for sailors with beds'''
        no_beds = df[df.bed == 0]
        for col in self.columns[4:-1]:
            if col in no_beds.columns:
                err = f"applying {col} to a sailor without a bed. "
                err += "Only sailors assigned to beds can receive treatment."
                assert np.all(no_beds[col].values==0), err

    def _verify_combo_constraints(self, df):
        '''verify that oxygen cannot be used with ventilators constraints'''
        vent = df[df.ventilator != 0]
        if 'oxygen' in df.columns:
            err = f"cannot combine oxygen with ventilators"
            assert np.all(vent['oxygen'].values==0), err

    def _calc_total(self, df):
        '''calculate totals to ensure they are correct'''
        df['_total'] = df.drop(['id', 'total'], axis=1).sum(axis=1)

    def _calc_bonus(self, df, name, qty, eff):
        '''calculate bonus for conserved treatment'''
        try:
            num_used = (df[name] != 0).astype(int).sum()
        except KeyError:
            num_used = 0
        num = qty - num_used
        bonus = int(eff * 0.5 * num)
        print(f"Bonus for {name} ({num} of {qty} remaining): {bonus}")
        return bonus

    def _calc_penalty(self, totals):
        '''calculate penalty for a sailor dying'''
        dead = (totals<=0).sum()
        penalty = dead * 50
        print(f"{dead} sailors died.  Penalty: -{penalty}")
        return penalty

    def _scorer(self, df, day_num):
        '''calculate and print total score for a given day'''
        self._calc_total(df)
        score = np.clip(df['_total'], 0, 100).sum()  # clip health btw 0 and 100
        print(f"Health total: {score}")
        score -= self._calc_penalty(df['_total'])
        for t in self.treatments:
            score += self._calc_bonus(df, *t)
        print(f"Total score: {score}")
        return score



if __name__=="__main__":

    grader = Grader(sys.argv[1],sys.argv[2])
    grader.validate_one()
