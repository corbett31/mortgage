"""Mortgage calculator

Using Halifax' mortgage rules, found here:
https://www.halifax.co.uk/mortgages/existing-customers/managing-your-mortgage

Functions:
strftime_suffix(format, date)
suffix(day)
isleap(year)
first_paydate(dayone, first_payday)
dailyrate(rate, year)
remaining_days(date)
mortgage_projector(self, mgage, term, monthly_payment, first_payday)

Classes:
Calendar()
MortgageInitiation(rate,
                   start_val,
                   dayone,
                   make_anyops,
                   make_maxops,
                   list_ops)
"""

import argparse
from datetime import datetime, timedelta

# Pass arguments to select predefined profiles
parser = argparse.ArgumentParser()
#parser.add_argument('-u', '--userinput', action='store_true')
parser.add_argument('-p', '--profile', type=str, default='userinput',
                    choices=['example', 'katandy', 'userinput'],
                    help='choose to manually input data with \'userinput\' '
                         'or from the predifined profiles: '
                         '\'example\', \'katandy\'')
args = parser.parse_args()

# Customise date suffixes
def strftime_suffix(format, date):
    """Add suffix to strftime"""
    return date.strftime(format).replace('{suf}',
                                         str(date.day) + suffix(date.day))

def suffix(day):
    """Identify the suffix of a day"""
    if 11 <= day <= 13:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

# My date format
my_date_format = '%A, {suf} %B \'%y' # Thursday, 26th March '20

def isleap(year):
    """Answer: is 'year' a leap year?"""
    if year % 4 == 0:
        return True
    elif year % 4 != 0:
        return False

def first_paydate(dayone, payday):
    """Compute the date of the first monthly payment."""
    if dayone.day <= payday:
        paymonth = dayone.month
        payear = dayone.year
    elif dayone.day > payday:
        paymonth = dayone.month + 1
        if dayone.year != 12:
            payear = dayone.year
        elif dayone.year == 12:
            payear = dayone.year + 1
    return datetime(payear, paymonth, payday)

def dailyrate(rate, year):
    """Convert percentage yearly rate to a fractional daily rate."""
    if year % 4 == 0:
        dr = rate * 0.01 / 366
    elif year % 4 != 0:
        dr = rate * 0.01 / 365
    return dr

def remaining_days(date):
    """Computes the number of days until the next 1st of the month.

    This number includes 'date' but excludes the 1st of the month.
    """
    if date.day != 1:
        yjump = date.year + (date.month // 12)
        mjump = (date.month + 1) % 12
        lastfew = datetime(yjump, mjump, 1) - date
        return lastfew.days
    else:
        return 0


class Calendar(object):
    """Calendars and permutations thereof."""

    def __init__(self):
        super(Calendar, self).__init__()
        self.days366 = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        self.days365 = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def leapcal(self, year):
        """Select the appropriate calenday for the year"""
        if year % 4 == 0:  # leap year
            cal = self.days366
        elif year % 4 != 0:
            cal = self.days365
        return cal

    def shufflecal(self, startmonth, startyear):
        """Shuffle startmonth to the front with preceding months behind."""
        if startmonth <= 2:
            cal = self.leapcal(startyear)
        elif startmonth > 2:
            cal = self.leapcal(startyear + 1)
        return cal[startmonth:] + cal[:startmonth]


class MortgageInitiation(object):
    """Case: Various Over Payments."""

    def __init__(self, dayone, rate, start_val, first_payday, monthly_payment,
                 make_anyops, make_maxops, list_ops=[]):
        super(MortgageInitiation, self).__init__()

        # Passed variables
        self.dayone = dayone
        self.rate = rate
        self.start_val = start_val
        self.first_payday = first_payday
        if first_payday.month == dayone.month:
            self.firstpayment = monthly_payment
        else: self.firstpayment = 0

        # Overpayment classifiers
        self.make_anyops = make_anyops
        self.make_maxops = make_maxops
        self.list_ops = list_ops

        # New variables
        self.first_op = self.over_pay(self.start_val, 0)
        self.baldue = self.start_val - self.first_op

        self.store_ops = []
        self.tally_ops(self.first_op)

        self.store_int = []
        self.tally_int(self.first_interest())

        # Update baldue
        self.baldue = self.baldue - self.firstpayment + self.first_interest()
        self.store_bal = []
        self.tally_bal(self.baldue)

    def over_pay(self, balance, year):
        """Sift from 'Nil', 'Max', and 'Varied' overpayments."""
        if self.make_anyops == False:
            return 0
        elif self.make_maxops == True:
            return 0.1 * balance
        else:
            return min(self.list_ops[year], 0.1 * balance)

    def first_interest(self):
        return remaining_days(self.dayone) * \
               dailyrate(self.rate, self.dayone.year) * \
               self.baldue - \
               remaining_days(self.first_payday) * \
               dailyrate(self.rate, self.first_payday.year) * \
               self.firstpayment


    def tally_ops(self, overpayment):
        self.store_ops.append(overpayment)

    def tally_int(self, interest):
        self.store_int.append(interest)

    def tally_bal(self, new_balance):
        self.store_bal.append(new_balance)


def mortgage_projector(mgage, rate, term, monthly_payment, first_payday):
    """Project mortgage over term."""

    # Instantiate Calender
    annual = Calendar()
    term_cal = []
    for yr in range(0,term):
        term_cal.extend(annual.shufflecal(
            first_payday.month, first_payday.year + yr))
    term_cal[-1] = mgage.dayone.day - 1

    for (mth, ndays) in enumerate(term_cal, start=first_payday.month):

        # We over pay on the 1st of each January
        if mth % 12 == 1:
            mth_overpayment = mgage.over_pay(mgage.baldue, mth//12)
            mgage.tally_ops(mth_overpayment)
        else: mth_overpayment = 0

        # Monthly interest accrued
        mth_interest = dailyrate(rate, first_payday.year + (mth//12)) * \
                       (mgage.baldue * ndays \
                        - mth_overpayment * (ndays-1) \
                        - monthly_payment * (max(0, ndays-first_payday.day)))
        mgage.tally_int(mth_interest)

        # New balance
        mgage.baldue = mgage.baldue + mth_interest - monthly_payment - \
                       mth_overpayment
        mgage.tally_bal(mgage.baldue)

    return mgage


if __name__ == '__main__':

    # Input automatice data: 'example'
    if args.profile == 'example':
        startdate = '04/07/2019'
        dayone = datetime.strptime(startdate, '%d/%m/%Y')
        rate = float(2)
        start_val = 200000
        term = 5
        monthly_payment = 800
        payday = 17
        first_payday = first_paydate(dayone, payday)
        effdur = term  # Set 'effective overpayment year counter'
        if (first_payday.year != 1) or (first_payday.year != 1):
            effdur = term + 1

        input_anyops = 'y'  # Would you like to make any overpayments?
        input_maxops = 'n'  # Would you like to make the maximum ammount?
        list_ops = [0, 5000, 6000, 10000, 11000, 8000]

    # Input automatice data: 'katandy'
    elif args.profile == 'katandy':
        startdate = '26/03/2020'
        dayone = datetime.strptime(startdate, '%d/%m/%Y')
        rate = 1.56
        start_val = 200000
        term = 5
        monthly_payment = 756.2
        payday = 1
        first_payday = first_paydate(dayone, payday)
        effdur = term  # Set 'effective overpayment year counter'
        if (first_payday.year != 1) or (first_payday.year != 1):
            effdur = term + 1

        input_anyops = 'y'  # Would you like to make any overpayments?
        input_maxops = 'n'  # Would you like to make the maximum ammount?
        list_ops = [0, 5000, 5000, 5000, 5000, 5000]

    # Input custom data:
    elif args.profile=='userinput':

        # First day
        dayone = datetime.strptime(input('Enter the date your mortgage begins '
                                       '[dd/mm/yyyy]:\n'), '%d/%m/%Y')

        # Interest rate
        rate = float(input(
            'Enter your mortgage interest rate as a percentage:\n'))

        # Starting value
        start_val = int(input(
            'Enter the initial value of your mortgage:\n'))

        # Mortgage term
        term = int(input(
            'Enter the mortgage product term in whole years:\n'))

        # Monthly payment
        monthly_payment = float(input(
            'Enter your monthly payment ammount:\n'))

        # Monthly payment date
        first_payday = first_paydate(dayone,int(input(
                'Enter the calendar day on which you will make your '
                'monthly payments [mm]:\n')))
        assert first_payday.day <= 28
        while first_payday.day > 28:
            first_payday = first_paydate(dayone, int(input(
                'Enter the calendar day on which you will make your '
                'monthly payments [mm]:\n')))

        # Any overpayments?
        input_anyops = input('Would you like to make any overpayments '
                             'during the mortgage term? [y/n]:\n')
        assert input_anyops == 'y' or input_anyops == 'n'

        # Maximum overpayments
        input_maxops = input(
                'Would you like to over pay maximally over the term; '
                'that is, 10% of the remaining balance per year? [y/n]:\n')
        assert input_maxops == 'y' or input_maxops == 'n'

        # Set 'effective overpayment year counter'
        effdur = term
        if (first_payday.year != 1) or (first_payday.year != 1):
            effdur = term + 1

        # Various overpayments
        if input_anyops == 'y' and input_maxops == 'n':
            list_ops = []
            for yr in range(effdur):
                list_ops.append(float(input('Enter the ammount you wish to over '
                                           'pay in year {:d}:\n'.format(yr))))


    # Introduce truth value make_anyops and extend list_ops to this case
    if input_anyops == 'n':
        make_anyops = False
        make_maxops = False
        list_ops = [0 for yr in range(effdur)]

    elif input_anyops == 'y':
        make_anyops = True

        # Introduce truth value make_maxops and extend list_ops to this case
        if input_maxops == 'y':
            make_maxops = True
            list_ops = []
        elif input_maxops == 'n':
            make_maxops = False

    
    # Initiate mortgage
    our_mgage = MortgageInitiation(dayone, rate, start_val, first_payday,
                                   monthly_payment, make_anyops,
                                   make_maxops, list_ops)
    max_mgage = MortgageInitiation(dayone, rate, start_val, first_payday,
                                   monthly_payment, True, True)
    nil_mgage = MortgageInitiation(dayone, rate, start_val, first_payday,
                                   monthly_payment, False, False)

    # Project mortgage over term
    our_result = mortgage_projector(our_mgage,
                                    rate,
                                    term,
                                    monthly_payment,
                                    first_payday)

    max_result = mortgage_projector(max_mgage,
                                    rate,
                                    term,
                                    monthly_payment,
                                    first_payday)

    nil_result = mortgage_projector(nil_mgage,
                                    rate,
                                    term,
                                    monthly_payment,
                                    first_payday)

    # Initial printout
    print('\nMortgage projection\n')
    print('Ammount borrowed: £{:,.2f}'.format(start_val))
    print('Annual interest rate: {:.4}%'.format(rate))
    print('Daily interest rate: {:.6%} (leap year), {:.6%} (short year)'
          .format(dailyrate(rate, 0), dailyrate(rate, 1)))
    print('')
    print(' - The first over payment of £{:,.2f} is paid on {:s}'.format(
            our_mgage.store_ops[0], strftime_suffix(my_date_format,
                                                 dayone)))

    if remaining_days(dayone) != 0:
        print('   In the first {0:d} days, £{1:,.2f} of interest accrued.'
              .format(remaining_days(dayone), our_mgage.store_int[0]))
    print('')

    # Intermediate printouts
    for (yr, op) in enumerate(our_mgage.store_ops[1:], start=1):
        print(' - An over payment of £{0:,.2f} is paid on {1:s}'
            .format(op, strftime_suffix(my_date_format,
                                        datetime(dayone.year + yr, 1, 1))))

        print('   The balance after the {:d}{} twelve months is £{:,.2f}'
              .format(yr, suffix(yr), sum(our_mgage.store_bal[12*(
                yr-1):12*yr])))
        print('')

    lastday = datetime(dayone.year + term, dayone.month, dayone.day) \
              - timedelta(days=1)
    print('End date: {}\n'
          .format(strftime_suffix(my_date_format, lastday)))

# Mortgage readout
print('Mortgage summary:')
print(' - Final balance is £{:,.2f}'.format(our_result.baldue))
print(' - The amount £{:,.2f} was paid in over payments'
      .format(sum(our_mgage.store_ops)))
print(' - The amount £{:,.2f} was paid in monthly payments'
      .format(monthly_payment * term * 12))
print(' - Total interest acrued was £{:,.2f}'
    .format(sum(our_result.store_int)))
print(' - This interest is on average £{:,.2f} per month\n'
      .format(sum(our_result.store_int) / (12 * term)))

# Maximum overpayment readout
if make_anyops==True and make_maxops == False:
    print('If maximum overpayments were made:')
    print(' - Final balance is £{:,.2f}'.format(max_result.baldue))
    print(' - The amount £{:,.2f} was paid in over payments'
          .format(sum(max_mgage.store_ops)))
    print(' - Total interest acrued was £{:,.2f}'
          .format(sum(max_result.store_int)))
    print(' - This interest is on average £{:,.2f} per month\n'
          .format(sum(max_result.store_int) / (12 * term)))

# Nill overpayment readout
if make_anyops==True and make_maxops == False:
    print('If no overpayments were made:')
    print(' - Final balance: £{:,.2f}'.format(nil_result.baldue))
    print(' - The amount £{:,.2f} was paid in over payments'
          .format(sum(nil_mgage.store_ops)))
    print(' - Total interest acrued: £{:,.2f}'.
          format(sum(nil_result.store_int)))
    print(' - This interest is on average £{:,.2f} per month\n'
          .format(sum(nil_result.store_int) / (12 * term)))

print('Time to remortgage\n')