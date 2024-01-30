from store.models import Product

class Cart():
    def __init__(self,request):
        self.session = request.session

        #get current session key if exist
        cart = self.session.get('session_key')
        
        #if user is newm no session key! create one!
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
        
        # make sure cart is available all parts of site
        self.cart = cart
        # onthor way is to use context processors
def add(self, product):
    product_id = str(product.id)

    if product_id in self.cart:
        pass
    else:
        self.cart[product_id] = {'price': str(product.price)}

    self.session.modified = True