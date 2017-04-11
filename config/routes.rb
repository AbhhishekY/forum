Rails.application.routes.draw do
  mount RailsEmailPreview::Engine, at: 'emails'
  devise_for :users
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
end
