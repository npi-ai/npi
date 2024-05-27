from npiai import app, NPI

npi = NPI()


@npi.function(description='demo')
def test():
    return 'Hello NPi!'


if __name__ == "__main__":
    print(npi.run(fn_name='test'))

    hw = app.time.create()
    print(hw.name())  # => time
    npi.add(hw)
    print(npi.run(fn_name='time/get_timezone', params={
        'test': 'Shanghai',
        'cases': ['case1', 'case2'],
    }))

    npi.add(hw)

    npi.server(port=19410)
